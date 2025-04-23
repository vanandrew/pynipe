"""Execution graph visualization for PyNipe."""

import html
import logging
from typing import Any

logger = logging.getLogger(__name__)


def create_execution_graph(workflow_results: dict[str, Any]) -> "ExecutionGraph":
    """
    Create an execution graph from workflow results.

    Parameters:
    -----------
    workflow_results : dict
        Results from a workflow execution

    Returns:
    --------
    ExecutionGraph
        Execution graph visualization
    """
    return ExecutionGraph(workflow_results)


class ExecutionGraph:
    """Execution graph visualization using mermaid.js."""

    def __init__(self, workflow_results: dict[str, Any]):
        """
        Initialize an execution graph.

        Parameters:
        -----------
        workflow_results : dict
            Results from a workflow execution
        """
        self.workflow_results = workflow_results

    def to_html(self, output_file: str) -> None:
        """
        Save the execution graph as an HTML file with mermaid.js visualization.

        Parameters:
        -----------
        output_file : str
            Path to output HTML file
        """
        try:
            # Extract tasks and their dependencies
            tasks, dependencies = self._extract_tasks_and_dependencies()

            # Generate mermaid diagram definition
            mermaid_diagram = self._generate_mermaid_diagram(tasks, dependencies)

            # Generate task details for the sidebar
            task_details = self._generate_task_details(tasks)

            with open(output_file, "w") as f:
                f.write(
                    f"""<!DOCTYPE html>
<html>
<head>
    <title>PyNipe Execution Graph</title>
    <script src="https://cdn.jsdelivr.net/npm/mermaid@11.6.0/dist/mermaid.min.js"></script>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 0;
            display: flex;
            height: 100vh;
        }}
        #sidebar {{
            width: 30%;
            padding: 20px;
            background-color: #f8f9fa;
            overflow-y: auto;
            border-right: 1px solid #dee2e6;
        }}
        #graph {{
            flex-grow: 1;
            padding: 20px;
            overflow: auto;
        }}
        .task-card {{
            border: 1px solid #dee2e6;
            border-radius: 5px;
            padding: 15px;
            margin-bottom: 15px;
            background-color: white;
        }}
        .task-header {{
            font-weight: bold;
            font-size: 1.1em;
            margin-bottom: 10px;
            padding-bottom: 5px;
            border-bottom: 1px solid #dee2e6;
        }}
        .task-status {{
            display: inline-block;
            padding: 3px 8px;
            border-radius: 3px;
            font-size: 0.8em;
            margin-left: 10px;
        }}
        .status-complete {{
            background-color: #d4edda;
            color: #155724;
        }}
        .status-failed {{
            background-color: #f8d7da;
            color: #721c24;
        }}
        .status-pending {{
            background-color: #fff3cd;
            color: #856404;
        }}
        .status-running {{
            background-color: #cce5ff;
            color: #004085;
        }}
        .task-property {{
            margin: 5px 0;
        }}
        .property-name {{
            font-weight: bold;
            color: #495057;
        }}
        .output-list {{
            margin-top: 5px;
            margin-bottom: 0;
            padding-left: 20px;
        }}
        .collapsible {{
            cursor: pointer;
        }}
        .content {{
            display: none;
            overflow: hidden;
        }}
        .mermaid {{
            font-size: 16px;
        }}
        h1 {{
            margin-top: 0;
            color: #343a40;
        }}
        .no-tasks {{
            color: #6c757d;
            font-style: italic;
        }}
    </style>
</head>
<body>
    <div id="sidebar">
        <h1>PyNipe Execution</h1>
        <div id="task-details">
            {task_details}
        </div>
    </div>
    <div id="graph">
        <pre class="mermaid">
{mermaid_diagram}
        </pre>
    </div>

    <script>
        // Initialize mermaid with a specific configuration
        mermaid.initialize({{
            startOnLoad: true,
            theme: 'default',
            securityLevel: 'loose',
            flowchart: {{
                htmlLabels: true,
                curve: 'basis'
            }}
        }});

        // Ensure mermaid renders after the page loads
        document.addEventListener('DOMContentLoaded', function() {{
            // Force mermaid to render
            mermaid.init(undefined, document.querySelectorAll('.mermaid'));

            // Add click handlers for collapsible sections
            var coll = document.getElementsByClassName("collapsible");
            for (var i = 0; i < coll.length; i++) {{
                coll[i].addEventListener("click", function() {{
                    this.classList.toggle("active");
                    var content = this.nextElementSibling;
                    if (content.style.display === "block") {{
                        content.style.display = "none";
                    }} else {{
                        content.style.display = "block";
                    }}
                }});
            }}
        }});
    </script>
</body>
</html>"""
                )
            logger.info(f"Execution graph saved to {output_file}")
        except Exception as e:
            logger.error(f"Failed to save execution graph: {e}")
            raise

    def _extract_tasks_and_dependencies(
        self,
    ) -> tuple[dict[str, dict[str, Any]], dict[str, set[str]]]:
        """
        Extract tasks and their dependencies from workflow results.

        Returns:
        --------
        tuple
            (tasks, dependencies) where:
            - tasks is a dict mapping task names to task info
            - dependencies is a dict mapping task names to sets of dependency task names
        """
        tasks = {}
        dependencies = {}

        # Get workflow if available
        workflow = self.workflow_results.get("workflow", None)

        # Extract tasks from workflow results
        if "tasks" in self.workflow_results:
            task_results = self.workflow_results.get("tasks", {})

            for task_name, outputs in task_results.items():
                # Get the task object from the workflow
                task_obj = None
                if workflow is not None and hasattr(workflow, "get_task_by_name"):
                    task_obj = workflow.get_task_by_name(task_name)

                # Create task info
                task_info = {
                    "name": task_name,
                    "status": "COMPLETE",  # Default status
                    "elapsed_time": None,
                    "command": None,
                    "outputs": outputs,
                    "inputs": {},  # Add inputs dictionary
                }

                # Add additional info if task object is available
                if task_obj is not None:
                    task_info["status"] = getattr(task_obj, "status", "COMPLETE")
                    task_info["elapsed_time"] = getattr(task_obj, "elapsed_time", None)
                    task_info["command"] = getattr(task_obj, "command", None)

                    # Extract dependencies
                    task_deps = getattr(task_obj, "dependencies", set())
                    dep_names = {dep.name for dep in task_deps if hasattr(dep, "name")}
                    dependencies[task_name] = dep_names

                    # Extract inputs
                    from ..core.task import TaskOutput

                    for input_name, input_value in getattr(task_obj, "inputs", {}).items():
                        if isinstance(input_value, TaskOutput):
                            # This is a dependency input (already shown as an edge)
                            task_info["inputs"][input_name] = {
                                "type": "task_output",
                                "task": input_value.task.name,
                                "output": input_value.output_name,
                            }
                        else:
                            # This is an external input
                            task_info["inputs"][input_name] = {
                                "type": "external",
                                "value": str(input_value),
                            }
                else:
                    dependencies[task_name] = set()

                tasks[task_name] = task_info

        return tasks, dependencies

    def _generate_mermaid_diagram(self, tasks: dict[str, dict[str, Any]], dependencies: dict[str, set[str]]) -> str:
        """
        Generate a mermaid.js flowchart diagram.

        Parameters:
        -----------
        tasks : dict
            Dict mapping task names to task info
        dependencies : dict
            Dict mapping task names to sets of dependency task names

        Returns:
        --------
        str
            Mermaid diagram definition
        """
        if not tasks:
            return 'graph TD\n    NoTasks["No tasks found"]:::noTasks'

        lines = ["graph TD"]

        # Define node styles based on status
        lines.append("    %% Node styles")
        lines.append("    classDef complete fill:#d4edda,stroke:#28a745,color:#155724")
        lines.append("    classDef failed fill:#f8d7da,stroke:#dc3545,color:#721c24")
        lines.append("    classDef pending fill:#fff3cd,stroke:#ffc107,color:#856404")
        lines.append("    classDef running fill:#cce5ff,stroke:#007bff,color:#004085")
        lines.append("    classDef noTasks fill:#f8f9fa,stroke:#6c757d,color:#6c757d")
        lines.append("    classDef input fill:#e2f0fb,stroke:#0d6efd,color:#0d6efd")

        # Add nodes for each task
        lines.append("\n    %% Task nodes")
        for task_name, task_info in tasks.items():
            # Create a safe ID for the node
            node_id = f"task_{task_name.replace(' ', '_')}"

            # Format elapsed time if available
            elapsed_time = ""
            if task_info.get("elapsed_time") is not None:
                elapsed_time = f"<br/>{task_info['elapsed_time']:.2f}s"

            # Create node label
            label = f"{task_name}{elapsed_time}"

            # Add node definition
            lines.append(f"    {node_id}[\"{label}\"]:::{task_info['status'].lower()}")

        # Input nodes removed as per user request - inputs are only shown in the sidebar

        # Add edges for dependencies
        if dependencies:
            lines.append("\n    %% Dependencies")
            for task_name, deps in dependencies.items():
                task_id = f"task_{task_name.replace(' ', '_')}"
                for dep in deps:
                    dep_id = f"task_{dep.replace(' ', '_')}"
                    lines.append(f"    {dep_id} --> {task_id}")

        return "\n".join(lines)

    def _generate_task_details(self, tasks: dict[str, dict[str, Any]]) -> str:
        """
        Generate HTML for task details sidebar.

        Parameters:
        -----------
        tasks : dict
            Dict mapping task names to task info

        Returns:
        --------
        str
            HTML for task details
        """
        if not tasks:
            return "<p class='no-tasks'>No tasks found in workflow results.</p>"

        html_parts = []

        for task_name, task_info in tasks.items():
            status = task_info.get("status", "COMPLETE")
            status_class = f"status-{status.lower()}"

            html_parts.append(
                f"""
        <div class="task-card" id="details-{task_name.replace(' ', '_')}">
            <div class="task-header">
                {html.escape(task_name)}
                <span class="task-status {status_class}">{status}</span>
            </div>
            <div class="task-property">
                <span class="property-name">Status:</span> {status}
            </div>"""
            )

            if task_info.get("elapsed_time") is not None:
                html_parts.append(
                    f"""
            <div class="task-property">
                <span class="property-name">Execution Time:</span> {task_info['elapsed_time']:.2f}s
            </div>"""
                )

            if task_info.get("command"):
                html_parts.append(
                    f"""
            <div class="task-property">
                <span class="property-name">Command:</span>
                <div class="collapsible">Show/Hide</div>
                <div class="content">
                    <pre>{html.escape(task_info['command'])}</pre>
                </div>
            </div>"""
                )

            # Add inputs section
            if task_info.get("inputs"):
                inputs = task_info["inputs"]
                html_parts.append(
                    f"""
            <div class="task-property">
                <span class="property-name">Inputs:</span> {len(inputs)} items
                <div class="collapsible">Show/Hide</div>
                <div class="content">
                    <ul class="output-list">"""
                )

                for input_name, input_info in inputs.items():
                    if input_info["type"] == "external":
                        value_str = input_info["value"]
                        if len(value_str) > 100:
                            value_str = value_str[:100] + "..."
                        html_parts.append(
                            f"""
                        <li><strong>{html.escape(input_name)}:</strong> {html.escape(value_str)}</li>"""
                        )
                    else:
                        html_parts.append(
                            f"""
                        <li><strong>{html.escape(input_name)}:</strong> From task {html.escape(input_info['task'])}, output {html.escape(input_info['output'])}</li>"""
                        )

                html_parts.append(
                    """
                    </ul>
                </div>
            </div>"""
                )

            if task_info.get("outputs"):
                outputs = task_info["outputs"]
                html_parts.append(
                    f"""
            <div class="task-property">
                <span class="property-name">Outputs:</span> {len(outputs)} items
                <div class="collapsible">Show/Hide</div>
                <div class="content">
                    <ul class="output-list">"""
                )

                for output_name, output_value in outputs.items():
                    output_str = str(output_value)
                    if len(output_str) > 100:
                        output_str = output_str[:100] + "..."
                    html_parts.append(
                        f"""
                        <li><strong>{html.escape(output_name)}:</strong> {html.escape(output_str)}</li>"""
                    )

                html_parts.append(
                    """
                    </ul>
                </div>
            </div>"""
                )

            html_parts.append(
                """
        </div>"""
            )

        return "\n".join(html_parts)
