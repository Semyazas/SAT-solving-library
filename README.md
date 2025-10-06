# SAT solver project


This is my SAT solver project. It contains SAT solvers in ```src/``` and also experiments testing their performance in folder ```experiments/``` on [SATLIB benchmark problems](https://www.cs.ubc.ca/~hoos/SATLIB/benchm.html). So far there are implemented look_ahead and dpll solvers. This project is mainly for learning purposes.

# Installation
You can install package with solvers by running
```bash
pip install .
```

# Usage

If you want to decide whether problem is SAT using dpll solver, just invoke 
```bash
py -m solver.dpll_solver.dpll [d if file is in dimacs, if satlib then s] [path to file]
``` 
If you want to use look_ahead solver instead, just call
```bash
py -m solver.look_ahead_solver.look_ahead [d if file is in dimacs, if satlib then s] [path to file]
```
## Structure of project

We have 2 main folders in src, these folders are solvers and parser. Parser contains functions that read input files and make them into CNF. 

Solvers contains sorce code for solvers.
Each solver takes its propagate function as parameter on input for modularity. Possible propagate functions are in folder ```propagate/```.

### DPLL solver

DPLL solver takes as paramater its decision heuristic and function that chooses literal (either according to best score given by heuristics or some other critirea (for example random)). Decision heuristics are in folder ```decision_heuristic/```s

### Look ahead solver

Look ahead solver takes as additional parameter difference heuristic, which helps it choose literal on which to do look ahead operation. Difference heuristics are in folder ```decision_heuristics/```.

### Experiments

We have 2 sets of experiments. One is with dpll, other with look_ahead solver. In each of them we test how solver performs on SAT benchmark problems. They are located in ```experiments/``` folder.

If you want to run experiments just run

```bash
py experiments [output_file] [input_file] [a/w -- a means that we use adjacency lists, w means we use watched literals] [lc/jw/rand -- lc means we use number of occurences heuristics, jw means that we use Jeroslow-Wang heuristics, rand means we use random choice of decision literal] 
```
