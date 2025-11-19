import tkinter as tk
from tkinter import ttk, messagebox
import random
import sudoku_solver  # Importamos el backend
from typing import List, Optional, Tuple
import os

# --- Constantes de Configuración ---
# Define los tamaños de Sudoku (N) y la dificultad
SUDOKU_SIZES = { "4x4 (N=2)": 2, "9x9 (N=3)": 3 }
DIFFICULTY_LEVELS = { 
    "Fácil": 0.40,  
    "Normal": 0.55, 
    "Difícil": 0.65 
}

# --- Clase Principal de la Aplicación ---
class SudokuApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Sudoku NxN - Clingo & DLV Solver")
        self.root.geometry("650x750")

        self.n = 3 # Tamaño de bloque (N=3 -> 9x9)
        self.s = 9 # Tamaño total (S=9)
        self.entries: List[List[tk.Entry]] = []
        self.full_solution: Optional[sudoku_solver.Grid] = None
        self.puzzle_grid: sudoku_solver.Grid = []
        
        # Variables de control
        self.size_var = tk.StringVar(value="9x9 (N=3)")
        self.diff_var = tk.StringVar(value="Normal")
        self.solver_var = tk.StringVar(value="clingo")

        self.setup_ui()
        self.new_game()

    def setup_ui(self):
        # --- Frame de Controles ---
        ctrl_frame = ttk.Frame(self.root, padding=10)
        ctrl_frame.pack(fill="x")
        
        # Selectores
        ttk.Label(ctrl_frame, text="Tamaño:").pack(side="left")
        ttk.OptionMenu(ctrl_frame, self.size_var, "9x9 (N=3)", *SUDOKU_SIZES.keys(), command=self.on_size_change).pack(side="left", padx=5)
        
        ttk.Label(ctrl_frame, text="Dificultad:").pack(side="left")
        ttk.OptionMenu(ctrl_frame, self.diff_var, "Normal", *DIFFICULTY_LEVELS.keys()).pack(side="left", padx=5)

        ttk.Label(ctrl_frame, text="Solver:").pack(side="left")
        ttk.OptionMenu(ctrl_frame, self.solver_var, "clingo", "clingo", "dlv").pack(side="left", padx=5)

        # --- Tablero ---
        self.grid_frame = ttk.Frame(self.root, padding=10)
        self.grid_frame.pack(expand=True, fill="both")

        # --- Botones ---
        btn_frame = ttk.Frame(self.root, padding=10)
        btn_frame.pack(fill="x")
        
        ttk.Button(btn_frame, text="Nuevo Juego", command=self.new_game).pack(side="left", expand=True, padx=5)
        ttk.Button(btn_frame, text="Pista", command=self.give_hint).pack(side="left", expand=True, padx=5)
        ttk.Button(btn_frame, text="Resolver", command=self.solve_game).pack(side="left", expand=True, padx=5)
        ttk.Button(btn_frame, text="Reiniciar", command=self.reset_board).pack(side="left", expand=True, padx=5)

    def on_size_change(self, val):
        """Actualiza N y S cuando el usuario cambia el tamaño."""
        self.n = SUDOKU_SIZES[val]
        self.s = self.n * self.n
        self.new_game()

    def draw_grid(self):
        """Dibuja la cuadrícula del Sudoku con bloques resaltados."""
        for widget in self.grid_frame.winfo_children(): widget.destroy()
        self.entries = []
        
        font_size = 18 if self.s > 4 else 22
        
        # Frames para los bloques (para las líneas gruesas)
        for br in range(self.n):
            for bc in range(self.n):
                f = tk.Frame(self.grid_frame, bd=2, relief="solid")
                f.grid(row=br, column=bc, sticky="nsew", padx=1, pady=1)
                
                # Celdas dentro del bloque
                for ir in range(self.n):
                    for ic in range(self.n):
                        r, c = br*self.n + ir, bc*self.n + ic
                        
                        # Definición de la validación de entrada
                        validate_cmd = (self.root.register(self.validate_input), "%P", "%S", "%d")

                        e = tk.Entry(
                            f, 
                            width=3, 
                            font=("Arial", font_size, "bold"), 
                            justify="center", 
                            bd=1, 
                            relief="sunken",
                            validate="key",
                            validatecommand=validate_cmd
                        )
                        e.grid(row=ir, column=ic, padx=1, pady=1)
                        if len(self.entries) <= r: self.entries.append([])
                        self.entries[r].append(e)
        
        # Asegurar que los bloques se expandan
        for i in range(self.n):
            self.grid_frame.rowconfigure(i, weight=1)
            self.grid_frame.columnconfigure(i, weight=1)

    def validate_input(self, P: str, S: str, d: str) -> bool:
        """Permite solo números válidos para el tamaño S."""
        if d == '0':  # Permitir borrado
            return True
        if not S.isdigit(): # Solo números
            return False
        
        # Verifica si el valor es válido (de 1 a S)
        if len(P) > 1: return False
        try:
            num = int(S)
            return 1 <= num <= self.s
        except ValueError:
            return False

    def new_game(self):
        """Genera y carga un nuevo puzzle."""
        self.draw_grid()
        try:
            self.full_solution = sudoku_solver.generate_solved_grid(self.n, self.s)
            if not self.full_solution:
                raise Exception("No se pudo generar una solución completa del Sudoku.")
            
            diff = DIFFICULTY_LEVELS[self.diff_var.get()]
            self.puzzle_grid = sudoku_solver.create_puzzle(self.full_solution, self.s, diff)
            self.update_ui(self.puzzle_grid)
        except Exception as e:
            messagebox.showerror("Error", f"Fallo al generar juego: {e}")

    def update_ui(self, grid: sudoku_solver.Grid, solution: bool = False):
        """Actualiza las celdas de la GUI con los valores del grid."""
        for r in range(self.s):
            for c in range(self.s):
                e = self.entries[r][c]
                val = grid[r][c]
                e.delete(0, "end")
                e.config(state="normal", fg="black")
                
                if val != 0:
                    e.insert(0, str(val))
                    
                    is_original = self.puzzle_grid[r][c] == val and val != 0
                    
                    if not solution and is_original:
                         # Los números iniciales se deshabilitan y se colorean de azul
                         e.config(state="disabled", disabledforeground="#3333AA")
                    elif solution:
                         # La solución final se muestra en verde
                         e.config(state="disabled", disabledforeground="darkgreen")
                    else:
                         # Números introducidos por pista o por el usuario (si está habilitado)
                         e.config(state="normal", fg="black")


    def solve_game(self):
        """Resuelve el puzzle actual usando el solver seleccionado."""
        solver = self.solver_var.get()
        try:
            # Usamos el puzzle original para asegurar una solución única
            if solver == "clingo":
                result = sudoku_solver.solve_with_clingo(self.puzzle_grid, self.n, self.s)
            elif solver == "dlv":
                result = sudoku_solver.solve_with_dlv(self.puzzle_grid, self.n, self.s)
            
            if result:
                self.full_solution = result # Almacena la solución oficial
                self.update_ui(result, solution=True)
                messagebox.showinfo("¡Resuelto!", f"El Sudoku ha sido resuelto usando {solver}.")
            else:
                messagebox.showwarning("Sin Solución", f"El solver ({solver}) no encontró una solución para este puzzle.")
        except Exception as e:
            messagebox.showerror(f"Error en {solver}", str(e))

    def give_hint(self):
        """Da una pista rellenando una celda vacía con el valor correcto."""
        if not self.full_solution: 
            messagebox.showwarning("Pista", "Genera un 'Nuevo Juego' primero.")
            return

        # Busca celdas vacías y editables (estado 'normal')
        empty: List[Tuple[int, int]] = []
        for r in range(self.s):
            for c in range(self.s):
                # Usamos get() para verificar si está vacía, e.config('state')[-1] para verificar si es editable
                if self.entries[r][c]['state'] == 'normal' and not self.entries[r][c].get():
                    empty.append((r, c))

        if empty:
            r, c = random.choice(empty)
            correct_val = self.full_solution[r][c]
            
            e = self.entries[r][c]
            e.insert(0, str(correct_val))
            e.config(fg="darkgreen")
        else:
            messagebox.showinfo("Pista", "¡El tablero está completo!")

    def reset_board(self):
        """Vuelve a cargar solo los números originales del puzzle, borrando la entrada del usuario."""
        self.update_ui(self.puzzle_grid)

def verify_files():
    """Verifica si los archivos de reglas existen."""
    files_ok = True
    # Solo verificamos si los archivos están presentes, los errores de ejecutable los maneja el solver.py
    for f in [sudoku_solver.CLINGO_FILE, sudoku_solver.DLV_FILE]:
        if not os.path.exists(f):
            print(f"ADVERTENCIA: Falta el archivo de reglas: {f}")
            files_ok = False
    if not files_ok:
        messagebox.showwarning(
            "Archivos de Reglas Faltantes",
            "Faltan uno o más archivos de reglas (.lp o .dlv).\n"
            "Asegúrate de que 'sudoku_clingo.lp' y 'sudoku_dlv.dlv' estén en la misma carpeta."
        )

if __name__ == "__main__":
    verify_files()
    
    root = tk.Tk()
    app = SudokuApp(root)
    root.mainloop()