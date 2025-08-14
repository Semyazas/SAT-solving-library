This is my SAT solver repo. It contains DPLL solver in file dpll. If you want to decide whether problem is SAT, just invoke "py dpll [-d if file is in dimacs, if satlib then -s] [name of file]".

DPLL solver takes its propagate function as an input for modularity. Possible propagate functions are in folder propagate.

It also takes as input decision heuristic and function that chooses literal (either according to best score given by heuristics or some other critirea (for example random)).

If you want to run experiments just run "py experiments [output_file] [input_file] [a/w -- a means that we use adjacency lists, w means we use watched literals] [lc/jw/rand -- lc means we use number of occurences heuristics, jw means that we use Jeroslow-Wang heuristics, rand means we use random choice of decision literal] "
