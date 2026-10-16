import { useEffect, useState } from "react";
import CytoscapeComponent from "react-cytoscapejs";
import "./GraphView.css";

const API = "http://127.0.0.1:8000";


function extractEntityIds(evidence = []) {
  const ids = new Set();
  const idPattern =
    /^(sys|person|team|decision|incident|doc|project|technology)_[a-z0-9_]+$/i;

  function scan(value) {
    if (!value) return;

    if (typeof value === "string") {
      if (idPattern.test(value)) ids.add(value);
      return;
    }

    if (Array.isArray(value)) {
      value.forEach(scan);
      return;
    }

    if (typeof value === "object") {
      Object.entries(value).forEach(([key, item]) => {
        if (
          typeof item === "string" &&
          (key === "id" || key.endsWith("_id")) &&
          idPattern.test(item)
        ) {
          ids.add(item);
        }

        scan(item);
      });
    }
  }

  scan(evidence);
  return [...ids];
}


const COLORS = {
  Project: "#a78bfa",
  Person: "#60a5fa",
  Technology: "#fbbf24",
  Document: "#34d399",
  Team: "#fb923c",
  Decision: "#f472b6",
  System: "#22d3ee",
  Incident: "#f87171",
};

export default function GraphView({
  focusIds = [],
  dependencyPaths = [],
}) {
  const [elements, setElements] = useState([]);
  const [selectedNode, setSelectedNode] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [visibleTypes, setVisibleTypes] = useState(
    Object.keys(COLORS)
    );
  
const [selectedEdge, setSelectedEdge] = useState(null);



  useEffect(() => {
    async function loadGraph() {
      try {
        const response = await fetch(`${API}/api/graph`);

        if (!response.ok) {
          throw new Error(`Graph API returned ${response.status}`);
        }

        const data = await response.json();
        setElements([...data.nodes, ...data.edges]);
      } catch (err) {
        setError(err.message || "Unable to load the knowledge graph.");
      } finally {
        setLoading(false);
      }
    }

        loadGraph();
    }, []);

  
    const [cyInstance, setCyInstance] = useState(null);

    
    useEffect(() => {
    if (!cyInstance) return;

    const cy = cyInstance;

    cy.elements().removeClass("focused dimmed focus-edge");

    const validFocusIds = focusIds.filter(
        (id) => cy.getElementById(id).length > 0
    );

    if (validFocusIds.length > 0) {
        const focusedNodes = cy.collection(
          validFocusIds.map((id) => cy.getElementById(id))
        );

        cy.elements().addClass("dimmed");
        focusedNodes.addClass("focused").removeClass("dimmed");
    }

    for (const path of dependencyPaths) {
        const target = cy.getElementById(path.target);

        if (target.length === 0) continue;

        const systems = [...path.affected].sort(
        (a, b) => a.depth - b.depth
        );

        const orderedNodes = [target];

        for (const system of systems) {
         const node = cy.getElementById(system.id);
          if (node.length > 0) orderedNodes.push(node);
        }

        for (let i = 0; i < orderedNodes.length - 1; i++) {
        const source = orderedNodes[i];
        const destination = orderedNodes[i + 1];

        const edge = source.edgesTo(destination).filter(
            (item) => item.data("label") === "DEPENDS_ON"
        );

        if (edge.length > 0) {
            source.removeClass("dimmed").addClass("focused");
            destination.removeClass("dimmed").addClass("focused");
            edge.removeClass("dimmed").addClass("focus-edge");
        }
        }
    }
    }, [cyInstance, focusIds, dependencyPaths]);



  const stylesheet = [
    {
      selector: "node",
      style: {
        label: "data(label)",
        "background-color": "data(color)",
        color: "#e5e7eb",
        "font-size": 12,
        "text-wrap": "wrap",
        "text-max-width": 140,
        "text-valign": "bottom",
        "text-margin-y": 10,
        width: 38,
        height: 38,
        "border-width": 1,
        "border-color": "#64748b",
      },
    },
    
    {
      selector: "edge",
      style: {
        width: 1.5,
        "line-color": "#475569",
        "target-arrow-color": "#64748b",
        "target-arrow-shape": "triangle",
        "arrow-scale": 0.8,
        "curve-style": "bezier",
        label: "",
        "font-size": 7,
      },
    },

    {
      selector: "node:selected",
      style: {
        "border-width": 4,
        "border-color": "#a3e635",
        "overlay-opacity": 0,
      },
    },
    
    {
      selector: ".dimmed",
      style: {
        opacity: 0.12,
    },
    },
    {
      selector: "node.focused",
      style: {
        opacity: 1,
        "border-width": 4,
        "border-color": "#a3e635",
        "z-index": 10,
    },
    },
    {
      selector: "edge.focus-edge",
      style: {
      opacity: 1,
      width: 3,
        "line-color": "#a3e635",
        "target-arrow-color": "#a3e635",
        "z-index": 10,
      },
    },
    
    {
    selector: ".filtered-out",
    style: {
        display: "none",
    },
    },


  ];

  
    const graphElements = elements.map((element) => {
    if (!element.data.source) {
        const type = element.data.type;

        return {
        ...element,
         data: {
         ...element.data,
            color: COLORS[type] || "#94a3b8",
        },
        classes: visibleTypes.includes(type) ? "" : "filtered-out",
        };
    }

    return {
        ...element,
        classes: "",
    };
    });


  
    const handleGraphReady = (cy) => {
     cy.off("tap");

    cy.on("tap", "node", (event) => {
     setSelectedNode(event.target.data());
        setSelectedEdge(null);
    });

    cy.on("tap", "edge", (event) => {
        const edge = event.target;
        const source = edge.source().data();
        const target = edge.target().data();

        setSelectedNode(null);
        setSelectedEdge({
        ...edge.data(),
        sourceLabel: source.label || source.id,
        sourceId: source.id,
        targetLabel: target.label || target.id,
        targetId: target.id,
        });
    });

  cy.on("tap", (event) => {
    if (event.target === cy) {
      setSelectedNode(null);
      setSelectedEdge(null);
    }
  });
};


  if (loading) {
    return <div className="graph-status">Loading company knowledge graph...</div>;
  }

  if (error) {
    return (
      <div className="graph-status graph-error">
        Failed to load graph: {error}
        <button onClick={() => window.location.reload()}>Retry</button>
      </div>
    );
  }

  return (
    <div className="graph-page">
      <div className="graph-header">
        <div>
          <h2>Company Knowledge Graph</h2>
          <p>Explore entities and the relationships connecting them.</p>
        </div>

        <div className="graph-counts">
          <span>{elements.filter((e) => !e.data.source).length} nodes</span>
          <span>{elements.filter((e) => e.data.source).length} relationships</span>
        </div>
      </div>

      
    <div className="graph-legend graph-filters">
        <button
            className="graph-filter-button"
            onClick={() =>
            setVisibleTypes(
                visibleTypes.length === Object.keys(COLORS).length
                ? []
                : Object.keys(COLORS)
            )
            }
        >
            {visibleTypes.length === Object.keys(COLORS).length
            ? "Hide all"
            : "Show all"}
        </button>

        {Object.entries(COLORS).map(([type, color]) => {
            const isVisible = visibleTypes.includes(type);

            return (
            <button
                key={type}
                className={`graph-filter-button ${isVisible ? "active" : ""}`}
                onClick={() =>
                setVisibleTypes((previous) =>
                    isVisible
                    ? previous.filter((item) => item !== type)
                    : [...previous, type]
                )
                }
            >
                <i
                style={{
                    backgroundColor: color,
                        opacity: isVisible ? 1 : 0.3,
                }}
                />
                {type}
            </button>
            );
        })}
        </div>


      <div className="graph-workspace">
        <div className="graph-canvas">
          {elements.length > 0 ? (
            <CytoscapeComponent
              elements={graphElements}
              stylesheet={stylesheet}
              layout={{
                name: "cose",
                animate: true,
                animationDuration: 700,
                randomize: true,
                nodeRepulsion: 18000,
                idealEdgeLength: 180,
                edgeElasticity: 80,
                nestingFactor: 1.2,
                gravity: 0.15,
                numIter: 1500,
                padding: 70,
                }}

              cy={(cy) => {
                setCyInstance(cy);
                handleGraphReady(cy);
              }}
              style={{ width: "100%", height: "100%" }}
              minZoom={0.3}
              maxZoom={3}
            />
          ) : (
            <p className="graph-status">No graph data found.</p>
          )}
        </div>

        {selectedNode && (
          <aside className="graph-inspector">
            <button
              className="graph-close"
              onClick={() => setSelectedNode(null)}
              aria-label="Close node details"
            >
              ×
            </button>

            <span
              className="graph-type"
              style={{
                color: COLORS[selectedNode.type] || "#94a3b8",
              }}
            >
              {selectedNode.type || "Unknown"}
            </span>

            <h3>{selectedNode.label || selectedNode.id}</h3>

            <p className="graph-node-id">{selectedNode.id}</p>

            <h4>Properties</h4>

            <div className="graph-properties">
              {Object.entries(selectedNode.properties || {}).map(
                ([key, value]) => (
                  <div className="graph-property" key={key}>
                    <span>{key.replaceAll("_", " ")}</span>
                    <strong>
                      {typeof value === "object"
                        ? JSON.stringify(value)
                        : String(value)}
                    </strong>
                  </div>
                )
              )}
            </div>
          
          </aside>
        )}

        {/* Relationship inspector */}
        {selectedEdge && (
          <aside className="graph-inspector">
            <button
              className="graph-close"
              onClick={() => setSelectedEdge(null)}
              aria-label="Close relationship details"
            >
              ×
            </button>

            <span
              className="graph-type"
              style={{ color: "#a3e635" }}
            >
              Relationship
            </span>

            <h3>{selectedEdge.label || "Unknown relationship"}</h3>

            <h4>Source entity</h4>
            <p>{selectedEdge.sourceLabel}</p>
            <p className="graph-node-id">{selectedEdge.sourceId}</p>

            <div className="relationship-direction">↓</div>

            <h4>Target entity</h4>
            <p>{selectedEdge.targetLabel}</p>
            <p className="graph-node-id">{selectedEdge.targetId}</p>

            <h4>Relationship type</h4>
            <p>{selectedEdge.label || "Not specified"}</p>
          </aside>
        )}
      </div>
    </div>
  );
}
