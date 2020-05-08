# Subgraph

This is simple tool that plots subgraphs from pbtxt and pb files. This is especially useful for graphs that a too large to open in current graphvisualization tools like [Netron](https://github.com/lutzroeder/netron). By default it creates a subgraph using dot and graphviz. It has option to open the subgraph in Netron

## Example Usage :
  1. TO see all options
   ```
   > python pbsubgraph.py
   ```
  The ouput looks like below
   ```
   python <script>
		 -pbtxt <filename>  (pbtxt filename)
		 -pb    <filename>  (pb file name) 
		 -node  <nodename>  (Name of the sub node to show)
		 -level <levelno>   (recursive level to which show graph)
		 -gen_pbtxt <fname> (Generates pb file for subgraph)
                 -netron            (Generates subgrapb pbtxt and calls netron)
		 -stripname         (Strips long names in the box)
   ```

  2. To see a node upto 3 level(default) of fanin and fanout neighbors.
```
   > python pbsubgraph.py -pbtxt graph.pbtxt -node bert/encoder/layer_1/attention/output/dense/MatMul
```
Shows.
     [fig1](https://github.com/jojivk73/Tools/tree/master/pbsubgraph/example1.png)
  
  3. The above default options show the full name of each node. 
     So the graph can be big.To stip the long name add -stripname option
```
     > python pbsubgraph.py -pbtxt graph.pbtxt -node bert/encoder/layer_1/attention/output/dense/MatMul
```
Shows.
     [fig2](https://github.com/jojivk73/Tools/tree/master/pbsubgraph/example2.png)

  3. To see a node in netron upto 5 levels
```
     > python pbsubgraph.py \
             -pbtxt graph.pbtxt \
             -node bert/encoder/layer_1/attention/output/dense/MatMul \
             -level 5  \
             -netron 
```
Shows 
[fig3](https://github.com/jojivk73/Tools/tree/master/pbsubgraph/example3.png) .
This writes the subgraph to /tmp dir and invokes netron. So you can navigate netron for these nodes to check attributes.

