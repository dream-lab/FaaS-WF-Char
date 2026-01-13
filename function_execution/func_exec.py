import matplotlib.pyplot as plt
import matplotlib.ticker as tck
import sys
import os
import json
import matplotlib.patches as mpatches
from matplotlib.lines import Line2D
from datetime import datetime

import shutil
import numpy as np
import networkx as nx
import pathlib
import pprint
import argparse
import statistics

from typing import Any
from collections import defaultdict
from matplotlib.lines import lineStyles
from azure.storage.queue import QueueClient
from python.src.utils.classes.commons.logger import LoggerFactory
parser = argparse.ArgumentParser(
    prog="ProgramName",
    description="What the program does",
    epilog="Text at the bottom of help",
)
logger = LoggerFactory.get_logger(__file__, log_level="INFO")

regions = ['AWSCentralIndia','AWSEastUsa','AWSCentralEurope','AzSCentralIndia','AzSEastUsa','AzSCentralEurope','AzNCentralIndia','AzNEastUsa','AzNCentralEurope']
class XFBenchPlotter: 
    plt.rcParams['ytick.labelsize'] = 30
    plt.rcParams['xtick.labelsize'] = 30
    plt.rcParams['axes.titlesize'] = 30
    plt.rcParams['axes.labelsize'] = 30
    plt.rcParams['legend.fontsize'] = 30


    
    
    def __init__(self, workflow_directory: str, workflow_deployment_id: str, run_id: str, format: str):
        self.__workflow_directory = workflow_directory
        self.__workflow_deployment_id = workflow_deployment_id
        self.__run_id = run_id
        self.__xfaas_dag = self.__init__dag(pathlib.Path(self.__workflow_directory) / "dag.json")
        self.__format = format

        '''
        Constructed directories and paths
        '''
        self.__exp_directory = pathlib.Path(self.__workflow_directory) / self.__workflow_deployment_id / self.__run_id
        self.__artifacts_filepath = self.__exp_directory / "artifact.json"
        self.__logs_dir = self.__exp_directory / "logs"
        self.__plots_dir = self.__exp_directory / "plots"
        self.__plots_dir_upd = f"{self.__workflow_directory}/plots/overleaf"
        self.__plots_dir_upd2 = f"{self.__workflow_directory}/plots2/overleaf"

        # Create the logs and the plots directory
        if not os.path.exists(self.__logs_dir):
            os.makedirs(self.__logs_dir)

        if not os.path.exists(self.__plots_dir):
            os.makedirs(self.__plots_dir)

        if not os.path.exists(self.__plots_dir_upd):
            os.makedirs(self.__plots_dir_upd)
        
        if not os.path.exists(self.__plots_dir_upd2):
            os.makedirs(self.__plots_dir_upd2)

        '''
        Using provenance artifacts to construct the experiment configuration
        '''
        if not os.path.exists(self.__artifacts_filepath):
            raise FileNotFoundError(f"artifact.json Not Found under {self.__exp_directory}")
        
        '''
        Construct the experiment configuration from the artifacts
        '''
        with open(self.__artifacts_filepath, "r") as file:
            config = json.load(file)
        
        
        # TODO - create a function which generate the step_x and step_y from the exp_config
        self.__exp_conf = config.get("experiment_conf")
        self.__queue_name = config.get("queue_details").get("queue_name")
        self.__conn_str = config.get("queue_details").get("connection_string")
        self.__config = config
        
        '''
        Create an experiment description dictionary
        '''
        temp_conf = list(self.__exp_conf.values())[0]
        self.__exp_desc = dict(wf_name=temp_conf.get("wf_name"),
                               csp=temp_conf.get("csp"),
                               dynamism=temp_conf.get("dynamism"),
                               payload=temp_conf.get("payload_size"))
        

        self.__logfile = f"{self.__get_outfile_prefix()}_dyndb_items.jsonl"

        '''
        Get the data from the queue and push to the file
        NOTE - if you call this again and logfile exists then it won't pull from queue
        '''
        if not os.path.exists(self.__logs_dir / self.__logfile):
            self.__get_from_queue_add_to_file()


        # Constructor
    def __init__dag(self, user_config_path):
        __dag_config_data = dict() # dag configuration (picked up from user file)
        __nodeIDMap = {} # map: nodeName -> nodeId (used internally)
        __dag = nx.DiGraph() # networkx directed graph
        # throw an exception if loading file has a problem
        def __load_user_spec(user_config_path):
            with open(user_config_path, "r") as user_dag_spec:
                dag_data = json.load(user_dag_spec)
            return dag_data
        try:
            __dag_config_data = __load_user_spec(user_config_path)
            __workflow_name = __dag_config_data["WorkflowName"]
        except Exception as e:
            raise e
    
        index = 1
        for node in __dag_config_data["Nodes"]:
            nodeID = node["NodeId"]
            # TODO - add a better way to add node codenames to the DAG
            __nodeIDMap[node["NodeName"]] = nodeID
            __dag.add_node(nodeID,
                                NodeId=nodeID,
                                NodeName=node["NodeName"], 
                                Path=node["Path"],
                                EntryPoint=node["EntryPoint"],
                                MemoryInMB=node["MemoryInMB"],
                                Codename=node["Code"])
            index += 1

        # add edges in the dag
        for edge in __dag_config_data["Edges"]:
            for key in edge:
                for val in edge[key]:
                    __dag.add_edge(__nodeIDMap[key], __nodeIDMap[val])
        return __dag

    def __get_outfile_prefix(self):
        
        prefix = f"{self.__exp_desc.get('wf_name')}_{self.__exp_desc.get('csp')}_{self.__exp_desc.get('dynamism')}_{self.__exp_desc.get('payload')}"
        
        return prefix


    def get_timings_dict(self,csp):
        hardware_dict = dict()
        # logger.info("Getting timing distribution dictionary")
        logs = self.__get_provenance_logs()
        
        distribution_dict = dict(
            client_overheads=[],
            functions=defaultdict(list),
            edges=defaultdict(list),
            wf_invocation_id = []
        )

        for log in logs:
            wf_invocation_id = log["workflow_invocation_id"]
            distribution_dict["wf_invocation_id"].append(wf_invocation_id)
            distribution_dict["client_overheads"].append((int(log["invocation_start_time_ms"]) - int(log["client_request_time_ms"]))/1000)
            for u in [v for v in self.__xfaas_dag.nodes]:
                time_to_subtract = 0
                cpu_id = None
                if csp == "aws":
                    cpu_id = "Intel(R) Xeon(R) Processor @ 2.50GHz"
                if csp != "aws":
                    cpu_id = log["functions"][u]["cid"].split("_")[1]
                    
                exec_time = round((log["functions"][u]["end_delta"] - log["functions"][u]["start_delta"])/1000,2) # seconds
                distribution_dict["functions"][u].append(exec_time)
                if u in hardware_dict:
                    if cpu_id in hardware_dict[u]:
                        hardware_dict[u][cpu_id].append(exec_time)
                    else:
                        hardware_dict[u][cpu_id] = [exec_time]
                else:
                    hardware_dict[u] = {cpu_id: [exec_time]}
                
        
        return hardware_dict
    
    def __create_dynamo_db_items(self):
        # print("Creating DynamoDB items")
        dynamodb_item_list = []

        queue = QueueClient.from_connection_string(conn_str=self.__conn_str, queue_name=self.__queue_name)
        response = queue.receive_messages(visibility_timeout=3000)
        # print('Reading Queue')
        for message in response:
            queue_item = json.loads(message.content)
            metadata = queue_item["metadata"]
            # print(metadata)
            
            # Filtering based on workflow deployment id during creation itself
            if metadata["deployment_id"].strip() == self.__workflow_deployment_id:
                dynamo_item = {}
                invocation_id = f"{metadata['workflow_instance_id']}-{metadata['session_id']}"
                dynamo_item["workflow_deployment_id"] = metadata["deployment_id"]
                dynamo_item["workflow_invocation_id"] = invocation_id
                dynamo_item["client_request_time_ms"] = str(
                    metadata["request_timestamp"]
                )
                dynamo_item["invocation_start_time_ms"] = str(
                    metadata["workflow_start_time"]
                )

                # add session id to dynamo db
                dynamo_item["session_id"] = str(metadata["session_id"])

                dynamo_item["functions"] = {}
                for item in metadata["functions"]:
                    for key in item.keys():
                        dynamo_item["functions"][key] = item[key]

                dynamodb_item_list.append(dynamo_item)

        return dynamodb_item_list
    
    def __get_from_queue_add_to_file(self):
        logger.info(f"Getting Items from Queue - {self.__queue_name}")
        sorted_dynamo_items = sorted(self.__create_dynamo_db_items(), key=lambda x: int(x["client_request_time_ms"]))
        with open(self.__logs_dir / self.__logfile, "w") as file:
            for dynamo_item in sorted_dynamo_items:
                dynamo_item_string = json.dumps(dynamo_item) + "\n"
                file.write(dynamo_item_string)


    def __get_provenance_logs(self):
        # logger.info(f"Reading logfile {self.__logfile}")
        with open(self.__logs_dir / self.__logfile, "r") as file:
            loglines = [json.loads(line) for line in file.readlines()]
        return loglines
    


def all_data_plot(all_data,wf_name):
    colors = {
        "aws":"orange",
        "azs":"blue",
        "azn":"green"
    }
    color_map = {
        "Intel(R) Xeon(R) Processor @ 2.50GHz-aws":"#FFA500",
        "Intel(R) Xeon(R) Processor @ 2.90GHz-aws":"#FFC71B",
        "Intel(R) Xeon(R) Processor @ 3.00GHz-aws":"#FFDA46",
        "AMD EPYC-aws":"#FFEBA5",

        "AMD EPYC 7763 64-Core Processor-azs":"#007FFF",
        "Intel(R) Xeon(R) CPU E5-2673 v4 @ 2.30GHz-azs":"#6CB4EE",
        "Intel(R) Xeon(R) Platinum 8272CL CPU @ 2.60GHz-azs":"#0066b2",
        "Intel(R) Xeon(R) Platinum 8171M CPU @ 2.60GHz-azs":"#89CFF0",

        "Intel(R) Xeon(R) Platinum 8171M CPU @ 2.60GHz-azn":"#008000",
        "Intel(R) Xeon(R) CPU E5-2673 v4 @ 2.30GHz-azn":"#228B22",
        "Intel(R) Xeon(R) Platinum 8272CL CPU @ 2.60GHz-azn":"#00AB66",
        "AMD EPYC 7763 64-Core Processor-azn":"#71BC78"

    }

    legends = [
    mpatches.Patch(color='#FFA500', label='AWS Intel(R) Xeon(R) Processor @ 2.50GHz'),
    mpatches.Patch(color='#FFC71B', label='AWS Intel(R) Xeon(R) Processor @ 2.90GHz'),
    mpatches.Patch(color='#FFDA46', label='AWS Intel(R) Xeon(R) Processor @ 3.00GHz'),
    mpatches.Patch(color='#FFEBA5', label='AWS AMD EPYC'),

    mpatches.Patch(color='#007FFF', label='AzS AMD EPYC 7763 64-Core Processor'),
    mpatches.Patch(color='#6CB4EE', label='AzS Intel(R) Xeon(R) CPU E5-2673 v4 @ 2.30GHz'),
    mpatches.Patch(color='#0066b2', label='AzS Intel(R) Xeon(R) Platinum 8272CL CPU @ 2.60GHz'),
    mpatches.Patch(color='#89CFF0', label='AzS Intel(R) Xeon(R) Platinum 8171M CPU @ 2.60GHz'),

    mpatches.Patch(color='#008000', label='AzN Intel(R) Xeon(R) Platinum 8171M CPU @ 2.60GHz'),
    mpatches.Patch(color='#228B22', label='AzN Intel(R) Xeon(R) CPU E5-2673 v4 @ 2.30GHz'),
    mpatches.Patch(color='#00AB66', label='AzN Intel(R) Xeon(R) Platinum 8272CL CPU @ 2.60GHz'),
    mpatches.Patch(color='#71BC78', label='AzN AMD EPYC 7763 64-Core Processor')
    ]

    legends_label = [i.get_label() for i in legends]


    
    if wf_name == 'graph':
        fns_map = {
            "1":"GGEN",
            "2":"GBFT",
            "3":"GMST",
            "4":"PGRK",
            "5":"AGG",
        }
    else:
        fns_map = {
            "1":"FDAT",
            "2":"GRAY",
            "3":"FLIP",
            "4":"RTIM",
            "5":"RESZ",
            "6":"RNET",
            "7":"ANET",
            "8":"MNET",
            "9":"AGG"
        }
    for region in all_data:
        print(region)
        cpu_map = dict()
        fig,ax = plt.subplots()
        fig.set_figwidth(17)
        fig.set_figheight(17)
        ax.set_xlabel('Function')
        ax.set_ylabel('Time(s)')
        ax2 = ax.twinx()
        ax2.set_ylabel('Percentage of Executions')
        ax2.set_ylim(0,100)
        x_titles = []
        xx =  []
        c = 0
        k=0
        for fn in all_data[region]:
            for csp in all_data[region][fn]:
                for cpu in all_data[region][fn][csp]:
                    keyy = f"{cpu}-{csp}" 
                    if keyy not in cpu_map:
                        cpu_map[keyy] = str(k)
                        k+=1
                    x_titles.append(fns_map[fn] )
                    
                    xx.append(c)
                    c+=1

        print(cpu_map)
        c = 0
        perc = []
        all_list = []
        q1,q3 = [],[]
        clrs = []
        mrks = []
        for fn in all_data[region]:
            for csp in all_data[region][fn]:
                tot_execs = 0
                for cpu in all_data[region][fn][csp]:
                    tot_execs += len(all_data[region][fn][csp][cpu])
                
                for cpu in all_data[region][fn][csp]:
                    percentage = round(len(all_data[region][fn][csp][cpu])/tot_execs*100,2)
                    print(fns_map[fn], csp, cpu, statistics.median(all_data[region][fn][csp][cpu]), percentage)
                    all_list.append(statistics.median(all_data[region][fn][csp][cpu]))
                    q1.append(np.percentile(all_data[region][fn][csp][cpu],25))
                    q3.append(np.percentile(all_data[region][fn][csp][cpu],75))
                    perc.append(percentage)
                    keyy = f"{cpu}-{csp}"
                    clrs.append(color_map[keyy])
                    if "AMD" in cpu:
                        mrks.append('red')
                    else:
                        mrks.append('lightblue')
        print(len(xx), len(perc),len(all_list))
       
        if wf_name == 'graph' and region == 'EastUsa':
            ax.set_ylim(ymin=0,ymax=5)
            ax.legend(legends,legends_label,loc='upper left',prop={'size': 18})
        ax.bar(xx,all_list,color=clrs,width=0.5)
        ax.errorbar(xx,all_list,yerr=[q1,q3],capsize=5,color='lightgrey',ls="none")
        
        ax.set_ylim(ymin=0,ymax=2)
        ax.set_xticks(xx)
        if wf_name == 'image' and region == 'EastUsa' or region == 'CentralEurope':
            ax.set_xticklabels(x_titles,rotation=90,fontsize=15)
        else:
            ax.set_xticklabels(x_titles,rotation=90)
        for i in range(len(xx)):
            ax2.plot(xx[i], perc[i], 'X',color=mrks[i],markersize=12)
        print(cpu_map)
        
        ax.yaxis.set_minor_locator(tck.AutoMinorLocator())
        ax.xaxis.set_minor_locator(tck.AutoMinorLocator())
        ax.grid(axis="y", which="major", linestyle="-", color="grey")
        ax.grid(axis="y", which="minor", linestyle="--", color="lightgrey")
        ax.minorticks_on()
        ax.set_axisbelow(True)
        
        # ax.set_xticks(x_titles,rotation=90)
        plt.savefig(f"{OUTPUT_DIR}/{region}-{wf_name}.pdf")
        # plt.show()
def do_(paths_fname):
    print("[datacenter--hardware, total_time(s),Perc.Execs]")
    log_paths = []
    global_region_wise_dict = dict()
    i = 0
    global_region_wise_dict['CentralIndia'] = dict()
    global_region_wise_dict['EastUsa'] = dict()
    global_region_wise_dict['CentralEurope'] = dict()
    for line in open(paths_fname):
        log_paths.append(line.strip())
        user_dir = line.strip().split("~")[0]
        dep_id = line.strip().split("~")[1]

        plotter = XFBenchPlotter(user_dir, dep_id, "exp1", "pdf")
        csp = ''
        if i < 3:
            csp = "aws"
        elif i < 6:
            csp = "azs"
        else:
            csp = "azn"
        hardware_split_dict = plotter.get_timings_dict(csp)
        transformed_dict = dict()
        region = ''
        if i%3 == 0:
            region = "CentralIndia"
        elif i%3 == 1:
            region = "EastUsa"
        else:
            region = "CentralEurope"
        

        for fn in hardware_split_dict:
            if fn not in global_region_wise_dict[region]:
                global_region_wise_dict[region][fn] = dict()
            if csp not in global_region_wise_dict[region][fn]:
                global_region_wise_dict[region][fn][csp] = dict()
        
        for fn in hardware_split_dict:
            for cpu in hardware_split_dict[fn]:
                if cpu not in global_region_wise_dict[region][fn][csp]:
                    global_region_wise_dict[region][fn][csp][cpu] = hardware_split_dict[fn][cpu]
                # print(regions[i],fn, cpu, statistics.median(hardware_split_dict[fn][cpu]))
                if cpu not in transformed_dict:
                    transformed_dict[cpu] = dict()
                transformed_dict[cpu][fn] = hardware_split_dict[fn][cpu]
        
        
        grand_total = 0
        for hrd in transformed_dict:
            tot_len = 0
            for fn in transformed_dict[hrd]:
                tot_len += len(transformed_dict[hrd][fn])
            grand_total += tot_len
        
        for hrd in transformed_dict:
            tot_time = 0
            tot_len = 0
            for fn in transformed_dict[hrd]:
                tot_time += statistics.median(transformed_dict[hrd][fn])
                tot_len += len(transformed_dict[hrd][fn])
            
        i += 1
    return global_region_wise_dict

PARENT_DIRECTORY_PATH = '<PARENT_DIRECTORY_PATH>'
OUTPUT_DIR = '<OUTPUT_DIRECTORY_PATH>'
paths_fname_graph = f"{PARENT_DIRECTORY_PATH}/graph_cross_region_files.txt"

all_graph_data = do_(paths_fname_graph)
all_data_plot(all_graph_data, 'graph')
print('\n-------------------------------------------------------------------------------Graph Done, starting image-------------------------------------------------------------------------------\n')

paths_fname_image = f"{PARENT_DIRECTORY_PATH}/image_cross_region_files.txt"

all_image_data = do_(paths_fname_image)
all_data_plot(all_image_data, 'image')
