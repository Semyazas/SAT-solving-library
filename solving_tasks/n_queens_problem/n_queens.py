from pysat.solvers import Minisat22, Glucose3, Lingeling
from matplotlib import pyplot
import sys
import time
def var(i, j, N):
    return i * N + j + 1   # maps (row,col) → SAT var

def n_queens_cnf(N):
    clauses = []

    # Row constraints: one queen per row
    for i in range(N):
        row_vars = [var(i, j, N) for j in range(N)]
        # At least one
        clauses.append(row_vars)
        # At most one
        for j in range(N):
            for k in range(j+1, N):
                clauses.append([-row_vars[j], -row_vars[k]])

    # Column constraints: one queen per column
    for j in range(N):
        col_vars = [var(i, j, N) for i in range(N)]
        clauses.append(col_vars)  # at least one
        for i in range(N):
            for k in range(i+1, N):
                clauses.append([-col_vars[i], -col_vars[k]])

    # Diagonal constraints
    for i in range(N):
        for j in range(N):
            v1 = var(i, j, N)
            # same "slope /" diagonal
            for k in range(1, N):
                if i+k < N and j+k < N:
                    clauses.append([-v1, -var(i+k, j+k, N)])
                if i+k < N and j-k >= 0:
                    clauses.append([-v1, -var(i+k, j-k, N)])
    return clauses

def print_solution(solver):
    model = solver.get_model()
    # Extract board
    board = [["." for _ in range(N)] for _ in range(N)]
    for v in model:
        if v > 0:
            v -= 1
            i, j = divmod(v, size)
            board[i][j] = "Q"
    for row in board:
        print(" ".join(row))

# Example: Solve 8-Queens
if __name__ == "__main__":
    sizes = [ i for i in range(50,300,10)]
    data  = []
    y     = {"Minisat22":[], "Glucose3" : [], "Lingeling": []}  
    for size in sizes:
        tic = time.perf_counter()
        cnf = n_queens_cnf(size)

        solvers = [
            (Minisat22(bootstrap_with=cnf), "Minisat22"),
            (Glucose3(bootstrap_with=cnf), "Glucose3"),
            (Lingeling(bootstrap_with=cnf), "Lingeling")
        ]
        print("-"*20)
        for solver, s_name in solvers:
            SAT = solver.solve()
            toc = time.perf_counter()
            t = toc - tic
            print(s_name , " size: " ,size ," SAT: ", SAT)
            print("time: ", toc - tic)
            data.append((s_name,t))
            if SAT: 
                if  len(sys.argv) > 2 and sys.argv[2] == "p":
                    print_solution(solver)
            else:
                print("No solution")

            solver.delete()
            y[s_name].append(t)
        print("-"*20)

    pyplot.figure(figsize=(8,6))

    for key in y.keys():
        pyplot.plot(sizes, y[key], marker="o", label=key)

    pyplot.xlabel("Board size N")
    pyplot.ylabel("Time (s)")
    pyplot.title("N-Queens SAT solver comparison")
    pyplot.legend(title="Solver")
    pyplot.grid(True)

    pyplot.savefig("graph.png")
    pyplot.show()
