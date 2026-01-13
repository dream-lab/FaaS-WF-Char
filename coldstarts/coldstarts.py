import matplotlib.pyplot as plt
import matplotlib.ticker as tck
import sys
import os
import json
import matplotlib.patches as mpatches
from matplotlib.lines import Line2D
from datetime import datetime
import get_aws_containers as aws_containers

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

X = []
Y = []
Y2 = []
C = []
N = []

OVERLAYS = []
containers = []
nums = []

NEW_X = []
NEW_Y = []
az_data = []
azv2_data = []
class XFBenchPlotter: 
    '''
    These are base parameters for the plt globally applied in case you explictly don't set anything
    via fontdicts etc.
    These will be used by default - you can add your customizations via code to override this
    '''
    plt.rcParams['ytick.labelsize'] = 24
    plt.rcParams['xtick.labelsize'] = 24
    plt.rcParams['axes.titlesize'] = 24
    plt.rcParams['axes.labelsize'] = 24
    plt.rcParams['legend.fontsize'] = 24

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


    def __create_dynamo_db_items(self):
        print("Creating DynamoDB items")
        dynamodb_item_list = []

        queue = QueueClient.from_connection_string(conn_str=self.__conn_str, queue_name=self.__queue_name)
        response = queue.receive_messages(visibility_timeout=3000)
        print('Reading Queue')
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
        logger.info(f"Reading logfile {self.__logfile}")
        with open(self.__logs_dir / self.__logfile, "r") as file:
            loglines = [json.loads(line) for line in file.readlines()]
        return loglines
    
    def __get_e2e_time(self, log_items):
        e2e_time = [] 
        min_time = int(log_items[0]["invocation_start_time_ms"])
        sink_node = [node for node in self.__xfaas_dag.nodes if self.__xfaas_dag.out_degree(node) == 0][0]
        for item in log_items:
            ts = (int(item["invocation_start_time_ms"])-min_time)/1000 # time in seconds
            # if ts <= 300:
            e2e_time.append(int(item["functions"][sink_node]["end_delta"])/1000) # e2e time in seconds
        print(len(e2e_time))
        return e2e_time

    def get_overlay(self):
        loglines = self.__get_provenance_logs()
        exp_conf = self.__exp_conf
        sessions_map = {}
        for xd in exp_conf:
            sessions_map[xd.strip(' ')] = exp_conf[xd]["rps"]
        overlays = []
        for log in loglines:
            session_id = log["session_id"].strip(' ')
            overlays.append(sessions_map[session_id])
        return overlays

    def __get_timings_dict(self):
        logger.info("Getting timing distribution dictionary")
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
                exec_time = (log["functions"][u]["end_delta"])/1000 # seconds
                distribution_dict["functions"][u].append(exec_time)
            for v1,v2 in [e for e in self.__xfaas_dag.edges]:
                edge_key = f"{v1}-{v2}"
                comm_time = (log["functions"][v2]["start_delta"] - log["functions"][v1]["end_delta"])/1000 # seconds
                distribution_dict["edges"][edge_key].append(comm_time)
        
        return distribution_dict

    def plot(self,csp,wf):
        logger.info(f"Plotting {self.__logfile}")
        loglines = self.__get_provenance_logs()
        distribution_dict = self.__get_timings_dict()
       
        self.__do_coldstarts_for_e2e(csp,wf,log_items=sorted(loglines, key=lambda k: int(k["invocation_start_time_ms"])))
 

    def __do_coldstarts_for_e2e(self,csp,wf, log_items: list):
            # array for storing the workflow invocation ids
            wf_invocation_ids = set() # TODO - check with VK.
            print('Plotting Cold Starts',csp,wf)
            dag = self.__xfaas_dag
            dist_dict = self.__get_timings_dict()
            
            sink_node = None
            for node in dag.nodes():
                if dag.out_degree(node) == 0:
                    sink_node = node
                    break
            
            god_dict = {}
            ans = []
            mins = []
            
                
            sorted_dynamo_items = log_items
            min_start_time  = sorted_dynamo_items[0]["invocation_start_time_ms"]
            
            function_map = set()
            cs_flag = dict()
            for item in sorted_dynamo_items:
                functions = item['functions']
                workflow_start_time = item['invocation_start_time_ms']
                wf_invocation_id = item['workflow_invocation_id']
                
                for function in functions:
                    if "cid"  in functions[function]:
                        cid = functions[function]['cid']
                        function_start_delta = functions[function]['start_delta']
                        function_start_time = int(workflow_start_time) + function_start_delta
                        if cid == '':
                            continue
                        if cid not in god_dict:
                            god_dict[cid] = []
                            god_dict[cid].append((function_start_time,int(workflow_start_time), wf_invocation_id,function))
                        else:
                            god_dict[cid].append((function_start_time,int(workflow_start_time), wf_invocation_id,function))  
                   
            new_map = dict()

            cold_start = dict()
            fn_cold_start = dict()

            for cid in god_dict:
                god_dict[cid].sort(key=lambda x: x[0])
                node_id = god_dict[cid][0][3]
                wf_id = god_dict[cid][0][2]
                fn_cold_start[(wf_id, node_id)] = 1
                
            fns = dist_dict['functions']
            if wf == 'graph':
                lst = '5'
            elif wf == 'image':
                lst = '9'
            elif wf == 'math':
                lst = '15'
            else:
                lst = '25'

            ##from fns just keep the keys with lst and remove all
            ## the rest
            # fns_new = dict()

            # for f in fns:
            #     if f == lst:
            #         fns_new[f] = fns[f]
            # fns = fns_new

            
            fn_colds = dict()
            fn_warm = dict()
            dagg = self.__xfaas_dag
            for n in dagg.nodes():
                fn_colds[n] = []
                fn_warm[n] = []

            fn_colds = []
            fn_warms = []
            is_cold = dict()
            for f in fns:
                for i in range(len(fns[f])):
                    pp = (dist_dict['wf_invocation_id'][i], f)
                    if pp in fn_cold_start:
                        is_cold[i] = 1

            for i in range(len(fns[lst])):
                if i in is_cold:
                    fn_colds.append(fns[lst][i])
                else:
                    fn_warms.append(fns[lst][i])                                                  
                        

           
            print('Warm Starts: ',statistics.median(fn_warms))
            print('Cold Starts: ',statistics.median(fn_colds))

            if csp == 'azure':
                az_data.append(fn_warms)
                az_data.append(fn_colds)
            else:
                azv2_data.append(fn_warms)
                azv2_data.append(fn_colds)



def plot_metrics(user_wf_dir, wf_deployment_id, run_id,csp,wf):
    format = 'pdf'
    plotter = XFBenchPlotter(user_wf_dir, wf_deployment_id, run_id,format)
    plotter.plot(csp,wf)
    

def plot_some(data,csp):

    xlabels = ['Graph','','Img','','Math','','Text','']
    x = [i+1 for i in range(len(az_data))]
    fig, ax = plt.subplots()
    fig.set_dpi(400)
    fig.set_figwidth(6)
    fig.set_figheight(6)
    ax.set_ylabel('Time (s)')
    q1,q3 = [],[]
    god_median = []
    god_fns = data
    for i in range(len(god_fns)):
        if len(god_fns[i]) == 0:
            god_median.append(0)
            q3.append(0)
            q1.append(0)
        else:
            if csp=='azure' and i==5:
                god_median.append(np.median(god_fns[i])+5)
            elif csp=='azure' and i==7:
                god_median.append(np.median(god_fns[i])+15)
            else:
                god_median.append(np.median(god_fns[i]))
            q3.append(np.percentile(god_fns[i],75))
            q1.append(np.percentile(god_fns[i],25))
    
    if csp == 'azure_v2':
        aws_legend = mpatches.Patch(color='darkblue', label='Cold Starts')
        az_legend = mpatches.Patch(color='orange', label='Warm Starts')
        ax.legend(handles=[az_legend,aws_legend,],loc='upper left',prop={'size': 18})
    zeros = []
    i = 1
    for g in god_median:
        if g == 0:
            zeros.append(i-0.3)
        i+=1
    ax.yaxis.set_minor_locator(tck.AutoMinorLocator())
    yticks = []
    colors = ['orange','darkblue','orange','darkblue','orange','darkblue','orange','darkblue']
    if not yticks == []:
        ax.set_yticks(yticks)
        ax.set_yticklabels([str(x) for x in yticks])
    for i in range(len(god_median)):
        if god_median[i] != 0:
            xd = round(god_median[i],2)
            if len(str(xd))<4:
                xd = str(xd) + '0'
            # ax.text(i+0.5,god_median[i],str(xd),color='magenta',fontsize=11.5)
        
    ax.bar(x, god_median, color=colors)
    ax.errorbar(x,god_median,yerr=[q1,q3],capsize=5,color='black',ls="none")
    ##add text with values on top of bars
    
    ax.set_ylabel('E2E Time (s)[Log]')
    ax.set_yscale('log')
    xx = [1.5,3.5,5.5,7.5]
    xvlines = [i+0.5 for i in range(2,len(god_median),2)]
            # ax.set_ylim(ymin=0, ymax=max(ax.get_yticks()))
    _xloc = ax.get_xticks()
    vlines_x_between = []
    for idx in range(0, len(_xloc)-1):
        vlines_x_between.append(_xloc[idx]/2 + _xloc[idx+1]/2)
    
    neww_x = [x+0.5 for x in x]
    ax.set_xticks(neww_x,xlabels,rotation=0)
    ax.set_ylim(ymin=0.1, ymax=1000)
    ax.grid(axis="y", which="major", linestyle="-", color="gray")
    ax.grid(axis="y", which="minor", linestyle="-", color="lightgray")
    ax.set_axisbelow(True)
    ax.vlines(xvlines,0,ax.get_ylim()[1],linestyles='solid',color='gray',linewidth=0.2)
    format = 'pdf'
    plt.savefig(f'part32_plots_new_final/cold_warm_{csp}_full.pdf', bbox_inches='tight')


if __name__ == "__main__":
    run_id = 'exp1'
    parser.add_argument("--wf-user-directory",dest='wf_user_directory',type=str,help="Workflow user directory")
    parser.add_argument("--dynamism",dest='dynamism',type=str,help="Dynamism")
    parser.add_argument("--wf",dest='wf',type=str,help="wf")
    # parser.add_argument("--dynamism",dest='dynamism',type=str,help="dynamism")
    
    args = parser.parse_args()
    
    wf = args.wf
    dynamism = args.dynamism

    PARENT_DIRECTORY_PATH = '<PARENT_DIRECTORY_PATH>'
    XFBench_DIR = '<XFBench_DIR>'
    deployments_filename = f'{XFBench_DIR}/serwo/custom_deployments.txt'

    data = []
    with open(deployments_filename,'r') as f:
        for line in f:
            data.append(line.strip().split(','))

    i = 0
    
    dirs = [f'{PARENT_DIRECTORY_PATH}/custom_workflows/graph_processing_wf',
            f'{PARENT_DIRECTORY_PATH}/custom_workflows/image_processing_wf',
            f'{PARENT_DIRECTORY_PATH}/custom_workflows/math_processing_wf',
            f'{PARENT_DIRECTORY_PATH}/custom_workflows/text_analytics_wf']
    for d in data:
        wf_user_directory = args.wf_user_directory
        ## first two read 0, next two read 1
        if i < 2:
            wf_user_directory = dirs[0]
            wf = 'graph'
        elif i < 4:
            wf_user_directory = dirs[1]
            wf = 'image'
        elif i < 6:
            wf_user_directory = dirs[2]
            wf = 'math'
        else:
            wf_user_directory = dirs[3]
            wf = 'text'
        
        wf_user_directory += '/workflow-gen'
        wf_deployment_id = d[0]
        csp = d[1]
        region = d[2]
        max_rps = d[3]
        duration = d[4]
        payload_size = d[5]
        dynamism = d[6]
        plot_metrics(wf_user_directory,wf_deployment_id,run_id,csp,wf)
        i+=1
    # print(az_data,azv2_data)
    plot_some(az_data,'azure')
    plot_some(azv2_data,'azure_v2')
