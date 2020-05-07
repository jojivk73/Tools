
import sys

from graphviz import Digraph
import time
import os


import tensorflow as tf
from google.protobuf import text_format



edges_done = []
nodes_done =[]
stripname=False
pbfile=False
subgraph_pbtxt=None
names_to_orig ={}

def get_pbtxt_graph(ifile) :
  txt=ifile.read()
  lgraph = text_format.Parse(txt, tf.compat.v1.GraphDef())
  return lgraph

def get_pb_graph(ifile) :
  f = gfile.FastGFile(model_filename, 'rb')
  graph_def = tf.compat.v1.GraphDef()
  lgraph = graph_def.ParseFromString(f.read())
  #g_in = tf.import_graph_def(graph_def)
  return lgraph

def collect_graph_data_pb(ifile, txtfile):
  global names_to_orig
  #txt=ifile.read()
  #lgraph = text_format.Parse(txt, tf.compat.v1.GraphDef())

  if txtfile :
    lgraph = get_pbtxt_graph(ifile)
  else :
    lgraph = get_pb_graph(ifile)

  nodes ={} 
  edges ={} 
  descs ={} 
  fanouts={}
  strips =["list", "shape", "dim", "size:", "{", "}"]
  for node in lgraph.node :
  
    #nodes
    names_to_orig[node.name] = node
    nodes[node.name] = node.op
  
    #edges
    edgs=[]
    for inp in node.input :
      edgs.append(inp)
    edges[node.name] = edgs
 
    #get dims
    shapes =node.attr["_output_shapes"]
    dim ="["
    shapes = str(shapes)
    for strip in strips :
      shapes=shapes.replace(strip, ' ')
    for shape in shapes.split() :
      dim +=shape +","
    dim=dim[:-1]
    dim +="]"
  
    #descs
    typ = node.attr["T"]
    typs =str(typ).split()
    if len(typs) == 2 :
      dtype=typs[1]
    elif len(typs) ==0:
      dtype = "Missing"
    else :
      dtype = typs[0]

    descs[node.name] = "T="+str(dtype)+" "+str(node.op) +" "+str(dim)
    #print(node.name, descs[node.name])

 
  for node in nodes.keys() :
    for edge in edges[node] :
      if edge not in fanouts.keys():
        fanouts[edge] = []
      fanouts[edge].append(node)
        
  return nodes, edges, descs, fanouts

def show_edge(g, n1, n2, nodes, descs):
  global edges_done
  nedge = [n1, n2]
  if nedge not in edges_done :
    edges_done.append([n1, n2])
    show_node(g, n1, nodes, descs)
    show_node(g, n2, nodes, descs)
    g.edge(n1, n2)

def print_node(sg, nd) :
  global names_to_orig
  sg.write("node { \n")
  node = names_to_orig[nd]
  if node :
    sg.write(str(node))
  else :
    sg.write(nd)
  sg.write("}\n")

def show_node(g, n1, nodes, descs, clr="green"): 
  global nodes_done
  global stripname
  global pbfile
  global subgraph_pbtxt

  if n1 not in nodes_done:
    nodes_done.append(n1)
    if subgraph_pbtxt :
       print_node(subgraph_pbtxt, n1)
       return

    sdata = descs[n1].split()
    #print(descs[n1])
    dtype =sdata[0] 
    note = "{<f0>" + nodes[n1] + " | <f1> " + dtype + "}" 
    nlab = " |<f2> "
    if not stripname and pbfile:
      note +=nlab + str(n1) 
      nlab = " |<f3> "
    if pbfile and len(sdata) >= 3 :
      note = note +nlab+sdata[2]
    #print(note)
    g.node(n1, label=note, shape="record", color=clr)

def show_rec_fwd(cnode, nodes, edges, fanouts, descs, level, g) :
    #print ("Node :", cnode)
    if level == 0 :
      return
    if cnode not in nodes.keys():
      return
    if cnode not in fanouts.keys():
      return
    fouts = fanouts[cnode]
    for fout in fouts:
      show_node(g, fout, nodes, descs)
      show_rec_fwd(fout, nodes, edges, fanouts, descs, level-1, g)
      #show_rec_bwd(fout, nodes, edges, 1, g)
      show_rec_bwd(fout, nodes, edges, descs, 1, g)
      show_edge(g, cnode, fout, nodes, descs)

def show_rec_bwd(cnode, nodes, edges, descs, level, g, color="green"):
    #print ("Node :", cnode)
    if level == 0 :
      return
    if cnode not in nodes.keys():
      return
    show_node(g, cnode, nodes, descs, color)
    if cnode not in edges.keys():
      return
    for edge in edges[cnode]:
      show_rec_bwd(edge, nodes, edges, descs, level-1, g, "green")
      #print("Edge", edge)
      show_edge(g, edge, cnode, nodes, descs)
  
def show_selected_nodes(g, nodes, edges, descs, fanouts, shownodes, rec_level=4) :
  show_count=0
  for node in nodes.keys():
    nop = nodes[node]
    for shownode in shownodes :
      if show_count > 2 :
        break
      #if shownode in nodes[node]:
      #print(shownode, node) 
      if str(shownode).strip() == str(node).strip() :
        show_rec_bwd(node, nodes, edges, descs, rec_level, g, "red")
        show_rec_fwd(node, nodes, edges, fanouts, descs, rec_level, g)
        show_count +=1
           
  return g

gg = Digraph('G', filename='cluster.gv')


def show_help():
  print ("python <script>"
         "\n\t\t -pbtxt <filename>  (pbtxt filename)"
         "\n\t\t -pb    <filename>  (pb file name) "
         "\n\t\t -node  <nodename>  (Name of the sub node to show)"
         "\n\t\t -level <levelno>   (recursive level to which show graph)"
         "\n\t\t -gen_pbtxt <fname> (Generates pb file for subgraph)"
         "\n\t\t -stripname         (Strips long names in the box)")
  exit(1)

def get_args(argv) :
  argc = len(argv)
  ind =0 
  stripname =False
  rlevel = 3
  fname =""
  snode=""
  pbtxt = True
  outfile =None
  run_netron=False
  while ind <argc :
    arg = argv[ind]
    if str(arg) == "-pbtxt" :
      fname = str(argv[ind+1])
      ind +=1
    elif str(arg) == "-pb" :
      fname = str(argv[ind+1])
      pbtxt = False
      ind +=1
    elif str(arg) == "-level" :
      rlevel = int(argv[ind+1])
      ind +=1
    elif str(arg) == "-node" :
      snode = str(argv[ind+1])
      ind +=1
    elif str(arg) == "-stripname" :
      stripname = True
    elif str(arg) == "-gen_pbtxt" :
      outfile = str(argv[ind+1])
    elif str(arg) == "-netron" :
      run_netron=True
    elif str(arg) == "-help" :
      show_help()

    ind +=1


  return fname,snode,rlevel,stripname,pbtxt,outfile,run_netron


###########################################################
#
###########################################################

fname,snode,rec_level,stripname,pbtxt,outfile,run_netron=get_args(sys.argv)
if not fname or not snode:
  show_help()

print(fname,snode,rec_level,stripname,pbtxt)
ifile = open(fname)

if run_netron and not outfile :
  print("Info :Using tmp file for subgraph")
  outfile = "/tmp/netron_sub_graph.pbtxt"
if outfile :
  subgraph_pbtxt=open(outfile, "w")
  
snodes = [snode]
nodes, edges, descs, fanouts = collect_graph_data_pb(ifile, pbtxt)
gg = show_selected_nodes(gg, nodes, edges, descs, fanouts, snodes, rec_level)
print("Build Complete...!")
if subgraph_pbtxt :
  subgraph_pbtxt.close()
  print("Generated Subgraph pbtxt file:",outfile)
  if run_netron :
    netron_cmd = "netron "+outfile
    os.system(netron_cmd)
else :
  gg.render('cluster.gv', view=True)
  time.sleep(1)
  print("Render Complete...!")


