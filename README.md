# Moray - Hydraulic Circuit Diagram Simulator
This application is a hydraulic/electronic circuit simulator made in Python using the Pygame library.  

## Installation
Make sure Python is installed, preferably Python 3.12+. Installing Pygame is also required, how to do so can be found [here](https://www.pygame.org/wiki/GettingStarted).  
Once it is installed, the simulator can be started by running the `main.py` file, or by clicking on `run.bat`.

## Usage
Once the simulator is open, circuits can be drawn.  
Components can be clicked and dragged onto the grid, and can be rotated clockwise with `R`. Hold shift while rotating to rotate anticlockwise.  
Using the "Draw pipes" mode pipes can be drawn with mouse click and drag. To make bends, T-junctions, or cross junctions, pipes must be connected with fitting components. Without fittings pipes only connect with something head-on.  
Using the "Inspect" mode, components can be selected to view and alter their parameters.

Once a circuit has been drawn the "Simulate" button can be pressed to run the simulation. This simulation will calculate the water pressure and flow at all points in the circuit, and will visualize this with orbs moving at different rates.
