import ForceGraph2D from "react-force-graph-2d";

interface GraphProps {
  graphData: {
    nodes: any[];
    edges: any[];
  };
}

function RepositoryGraph({ graphData }: GraphProps) {
  const data = {
    nodes: graphData.nodes,
    links: graphData.edges
  };

  return (
    <div style={{ height: "600px", width: "100%", background: "#111", borderRadius: "8px", overflow: "hidden", marginTop: "20px" }}>
      <ForceGraph2D
        graphData={data}
        nodeLabel="label"
        nodeAutoColorBy="type"
      />
    </div>
  );
}

export default RepositoryGraph;
