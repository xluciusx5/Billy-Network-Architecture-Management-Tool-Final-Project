import os
import pandas as pd
import re
from datetime import datetime
from pyvis.network import Network

def extract_location(hostname):
    """Extracts the location from the hostname."""
    parts = hostname.split("-")
    if len(parts) >= 3:
        return f"{parts[1]}-{parts[2]}"  # Example: "EUN-OSL", "USC-POS"
    elif len(parts) == 2:
        return parts[1]  # Example: "ABZ"
    else:
        return "UNKNOWN"

def generate_network_diagram(filepath, output_folder):
    """Generates a structured and visually enhanced network diagram."""
    df = pd.read_excel(filepath, engine='openpyxl') if filepath.endswith(".xlsx") else pd.read_csv(filepath)

    # Ensure 'End of Life' column is a string, replacing NaT with 'Unknown'
    df['End of Life'] = df['End of Life'].astype(str).replace("NaT", "Unknown")

    # Generate Unique Diagram Name
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    diagram_filename = f"network_{timestamp}.html"
    diagram_path = os.path.join(output_folder, diagram_filename)

    # Initialize Pyvis Network
    net = Network(height="1000px", width="100%", bgcolor="#1E1E1E", font_color="white", directed=True)

    # Improved Layout & Spacing
    net.set_options("""
    {
      "layout": {
        "hierarchical": {
          "enabled": true,
          "levelSeparation": 250,  
          "nodeSpacing": 300,  
          "treeSpacing": 500,  
          "direction": "UD",
          "sortMethod": "directed"
        }
      },
      "nodes": {
        "borderWidth": 2,
        "size": 40,
        "color": {
          "highlight": {
            "border": "#F39C12",
            "background": "#F4D03F"
          }
        },
        "font": {
          "size": 18,
          "color": "white"
        }
      },
      "edges": {
        "width": 2,
        "color": {"inherit": "both"},
        "smooth": {
          "type": "dynamic"
        }
      },
      "physics": {
        "enabled": true,
        "barnesHut": {
          "gravitationalConstant": -3000,
          "centralGravity": 0.3,
          "springLength": 150,
          "damping": 0.3
        }
      }
    }
    """)

    # Device Categorization
    main_nodes = {}  # Firewalls/Routers
    switch_levels = {}  # Store switch levels
    switches = []  # Switches

    for _, row in df.iterrows():
        hostname = row["Hostname"]

        # Ensure hostname is a valid string
        if pd.isna(hostname) or hostname.strip() == "":
            hostname = "Unknown_Device"

        # Extract correct location from hostname
        location_code = extract_location(hostname)

        # Device Label (for tooltips)
        device_label = f"<b>{hostname}</b><br>Model: {row['Model Name']}<br>IP: {row['IP Address']}<br>EOL: {row['End of Life']}"

        # Categorize Devices
        if re.search(r"FG01|FW|RT|R01", hostname):  # Firewalls/Routers
            main_nodes[location_code] = hostname
            net.add_node(hostname, label=hostname, title=device_label, color="red", shape="hexagon", level=0)
        else:  # Switches
            switches.append((hostname, location_code, device_label))

    # Connect Switches to Their Main Nodes with Individual Levels
    for hostname, location_code, device_label in switches:
        # Assign switch a unique level
        if location_code not in switch_levels:
            switch_levels[location_code] = 1  # Start at level 1
        else:
            switch_levels[location_code] += 1  # Increment for each switch in the same location

        # Add switch to network
        net.add_node(hostname, label=hostname, title=device_label, color="grey", shape="box", level=switch_levels[location_code])

        # Find the best matching main node
        best_match = None
        for loc, main in main_nodes.items():
            if location_code.startswith(loc):
                best_match = main
                break

        if best_match:
            net.add_edge(best_match, hostname, color="white", arrows="to")
        else:
            print(f"⚠ Warning: No main node found for device {hostname} (Location: {location_code})")

    # Save & Return Network Diagram
    net.save_graph(diagram_path)
    return diagram_filename
