# Billy - Network Architecture Management Tool - Final Project Proof-of-Concept
This project introduces Billy, which is a web-based network architecture management tool purposely designed to assist network engineers to manage hardware inventories and network diagrams, together with performing firmware vulnerability security analysis. As opposed to focusing only on network diagramming, the project evolved in order to address a much critical gap in proactive security assessment in network infrastructures. Billy absorbs a dataset, designs a network diagram, performs live firewall interrogations via SSH and outputs a security risk prediction, making use of survival analysis machine learning. 

![Billy-Poster](https://github.com/user-attachments/assets/39801f92-e122-4039-8148-40550704e45b)

Pererequisites
 
Ensure you have the following installed:
 
    Python 3.14 (recommended)
 
    Git
 
    pip (Python package manager)
 
 Installation
 
    Clone the repository
 
Create a virtual environment (recommended)
 
Install required Python packages
 
    pip install -r requirements.txt
 
Project Structure
 
    app.py – Flask application entry point
 
    datasets/ – Folder for uploaded CSV/XLSX hardware files
 
    static/ – CSS styles, background image, and generated diagrams
 
    templates/ – HTML templates (home, report, network diagram, fetch firmware)
 
    utils/ – Helper modules:
 
        processing.py – Generates network diagrams
 
        ssh_fortigate.py – Fetches firmware via SSH
 
        vulnerability.py – ML model & prediction logic
 
Running the App
 
Start the Flask server:
 
python app.py
 
Then, open your browser and go to:
 
http://127.0.0.1:5000/
