import re
import tkinter as tk
from tkinter import messagebox, ttk
import subprocess
import math
import os
import random

# Verificar librería Clingo
try:
    import clingo
    CLINGO_AVAILABLE = True
except ImportError:
    CLINGO_AVAILABLE = False

class SudokuApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Proyecto FPL 2025 - Generador Universal NxN")
        
        # Variables iniciales
        self.n = 9 
        self.cells = {} 
        self.region_map = {}
        self.full_solution = {} 
        
        # Variables de control de la Interfaz
        self.mode = tk.StringVar(value="tradicional")
        self.difficulty = tk.StringVar(value="Medio")
        self.size_var = tk.StringVar(value="9") # Variable para controlar el tamaño (NxN)
        
        # --- PANEL IZQUIERDO (CONTROLES) ---
        control_frame = tk.Frame(root, bg="#e0e0e0", padx=10, pady=10)
        control_frame.pack(side=tk.LEFT, fill=tk.Y)
        
        # 1. Configuración de Tamaño (NUEVO REQUISITO)
        tk.Label(control_frame, text="TAMAÑO (NxN)", bg="#e0e0e0", font=("Arial", 10, "bold")).pack(pady=5)
        frame_size = tk.Frame(control_frame, bg="#e0e0e0")
        frame_size.pack(fill=tk.X)
        tk.Radiobutton(frame_size, text="9x9", variable=self.size_var, value="9", command=self.change_size, bg="#e0e0e0").pack(side=tk.LEFT, padx=10)
        tk.Radiobutton(frame_size, text="4x4", variable=self.size_var, value="4", command=self.change_size, bg="#e0e0e0").pack(side=tk.LEFT, padx=10)

        # 2. Tipo de Juego
        tk.Label(control_frame, text="TIPO DE JUEGO", bg="#e0e0e0", font=("Arial", 10, "bold")).pack(pady=(15,5))
        tk.Radiobutton(control_frame, text="A) Tradicional", variable=self.mode, value="tradicional", command=self.update_visuals, bg="#e0e0e0").pack(anchor="w")
        tk.Radiobutton(control_frame, text="B) Irregular (Color)", variable=self.mode, value="irregular", command=self.update_visuals, bg="#e0e0e0").pack(anchor="w")
        
        tk.Label(control_frame, text="Dificultad:", bg="#e0e0e0").pack(anchor="w", pady=(10,0))
        niveles = ["Fácil", "Medio", "Difícil"]
        self.combo_diff = ttk.Combobox(control_frame, values=niveles, state="readonly", textvariable=self.difficulty)
        self.combo_diff.pack(fill=tk.X, pady=2)
        self.combo_diff.current(1)

        # 3. Acciones
        tk.Label(control_frame, text="JUEGO", bg="#e0e0e0", font=("Arial", 10, "bold")).pack(pady=(15,5))
        tk.Button(control_frame, text="🎲 Generar Nuevo Juego", command=self.generate_game, bg="#ffcc80", font=("Arial", 9, "bold")).pack(fill=tk.X, pady=5)
        tk.Button(control_frame, text="Limpiar Tablero", command=self.clear_grid).pack(fill=tk.X, pady=2)

        # 4. Solucionadores
        tk.Label(control_frame, text="SOLVER (IA)", bg="#e0e0e0", font=("Arial", 10, "bold")).pack(pady=(20,5))
        tk.Button(control_frame, text="Resolver con CLINGO", command=lambda: self.solve_game(engine="clingo"), bg="lightblue").pack(fill=tk.X, pady=3)
        tk.Button(control_frame, text="Resolver con DLV", command=lambda: self.solve_game(engine="dlv"), bg="lightgreen").pack(fill=tk.X, pady=3)
        tk.Button(control_frame, text="💡 Dame una Pista", command=self.give_hint, bg="white").pack(fill=tk.X, pady=(10,2))

        # --- PANEL DERECHO (TABLERO) ---
        self.board_frame = tk.Frame(root, padx=20, pady=20)
        self.board_frame.pack(side=tk.RIGHT)
        
        # Iniciar dibujando el grid por defecto
        self.change_size()

    def change_size(self):
        # Esta función reconstruye todo el tablero cuando se cambia entre 9x9 y 4x4
        self.n = int(self.size_var.get())
        
        # Limpiar todo lo anterior
        for widget in self.board_frame.winfo_children():
            widget.destroy()
        self.cells = {}
        self.full_solution = {}
        
        # Crear casillas nuevas
        for r in range(1, self.n + 1):
            for c in range(1, self.n + 1):
                # Si es 4x4 usamos letra más grande para que se vea bien
                f_size = 24 if self.n == 4 else 18
                w_size = 6 if self.n == 4 else 4
                
                e = tk.Entry(self.board_frame, width=w_size, font=('Arial', f_size), justify='center')
                e.grid(row=r-1, column=c-1, padx=2, pady=2)
                self.cells[(r,c)] = e
        
        # Regenerar mapa de colores y actualizar
        self.generate_regions_map()
        self.update_visuals()

    def update_visuals(self):
        # Se asegura de tener el mapa correcto cargado
        self.generate_regions_map()
        
        for r in range(1, self.n + 1):
            for c in range(1, self.n + 1):
                rid = self.region_map.get((r,c), 1)
                bg = "white"
                
                if self.mode.get() == "irregular":
                    bg = self.get_color(rid)
                elif self.mode.get() == "tradicional":
                     # Calcula el color ajedrezado según el tamaño
                     if self.n == 9:
                         box_r, box_c = (r-1)//3, (c-1)//3
                     else: # Caso 4x4 (Bloques de 2x2)
                         box_r, box_c = (r-1)//2, (c-1)//2
                     
                     if (box_r + box_c) % 2 == 0: bg = "#f0f0f0"
                
                self.cells[(r,c)].config(bg=bg)

    def generate_regions_map(self):
        self.region_map = {}
        
        # --- LÓGICA PARA 9x9 ---
        if self.n == 9:
            if self.mode.get() == "tradicional":
                for r in range(1, 10):
                    for c in range(1, 10):
                        self.region_map[(r,c)] = ((r-1)//3)*3 + ((c-1)//3) + 1
            else:
                # MAPAS VALIDADOS
                mapa_1 = [
                    [1, 1, 1, 1, 1, 6, 7, 7, 7],
                    [1, 2, 1, 1, 6, 6, 7, 8, 7],
                    [1, 2, 6, 6, 6, 6, 9, 8, 7],
                    [2, 2, 2, 6, 9, 6, 9, 8, 7],
                    [3, 3, 2, 9, 9, 9, 9, 8, 7], 
                    [3, 2, 2, 9, 9, 4, 8, 8, 7],
                    [3, 3, 2, 4, 4, 4, 8, 8, 8],
                    [3, 3, 3, 4, 5, 4, 5, 5, 5],
                    [3, 4, 4, 4, 5, 5, 5, 5, 5]  
                ]
                mapa_2 = [
                    [1, 1, 1, 1, 1, 6, 7, 7, 7],
                    [1, 2, 2, 2, 1, 6, 7, 7, 7],
                    [1, 2, 2, 2, 5, 6, 6, 7, 7],
                    [1, 2, 4, 4, 5, 5, 6, 6, 7],
                    [2, 2, 4, 5, 5, 5, 6, 8, 8],
                    [3, 4, 4, 5, 5, 6, 6, 8, 9],
                    [3, 3, 4, 4, 5, 8, 8, 8, 9],
                    [3, 3, 3, 4, 9, 8, 8, 8, 9],
                    [3, 3, 3, 4, 9, 9, 9, 9, 9]
                ]
                mapa_3 = [
                    [1, 1, 1, 1, 2, 2, 2, 2, 3],
                    [4, 1, 1, 1, 1, 2, 2, 2, 3],
                    [4, 4, 4, 4, 1, 2, 2, 3, 3],
                    [5, 5, 4, 4, 4, 4, 3, 3, 8],
                    [5, 5, 5, 5, 7, 3, 3, 3, 8],
                    [5, 5, 7, 7, 7, 8, 8, 8, 8],
                    [6, 5, 7, 7, 7, 8, 9, 9, 8],
                    [6, 6, 7, 6, 7, 9, 9, 9, 8],
                    [6, 6, 6, 6, 6, 9, 9, 9, 9] 
                ]
                selected_map = random.choice([mapa_1, mapa_2, mapa_3])
                for r in range(1, 10):
                    for c in range(1, 10):
                        self.region_map[(r,c)] = selected_map[r-1][c-1]

        # --- LÓGICA PARA 4x4 (NUEVO) ---
        elif self.n == 4:
            if self.mode.get() == "tradicional":
                # Regiones cuadradas de 2x2
                for r in range(1, 5):
                    for c in range(1, 5):
                        self.region_map[(r,c)] = ((r-1)//2)*2 + ((c-1)//2) + 1
            else:
                # Mapas Irregulares pequeños válidos (4 celdas por región)
                mapa_4A = [
                    [1, 1, 1, 1],
                    [2, 2, 2, 3],
                    [2, 4, 3, 3],
                    [4, 4, 4, 3]
                ]
                mapa_4B = [
                    [1, 1, 2, 4],
                    [1, 2, 2, 4],
                    [1, 3, 2, 4],
                    [3, 3, 3, 4]
                ]
                mapa_4C = [
                    [1, 2, 2, 2],
                    [1, 2, 3, 4],
                    [1, 3, 3, 4],
                    [1, 3, 4, 4]
                ]
                mapa_4D = [
                    [1, 1, 1, 2],
                    [1, 2, 2, 2],
                    [4, 3, 3, 3],
                    [4, 4, 4, 3]
                ]
                selected_map = random.choice([mapa_4A, mapa_4B, mapa_4C, mapa_4D])
                for r in range(1, 5):
                    for c in range(1, 5):
                        self.region_map[(r,c)] = selected_map[r-1][c-1]

    def get_color(self, region_id):
        colors = ["#FF9AA2", "#B5EAD7", "#C7CEEA", "#FFDAC1", "#E2F0CB", "#FFB7B2", "#90CCE4", "#F3Dfd1", "#D8BFD8"]
        return colors[(region_id - 1) % 9]

    def get_facts(self):
        facts = []
        for (r,c), entry in self.cells.items():
            val = entry.get()
            if val.isdigit():
                facts.append(f"inicial({r},{c},{val}).")
            rid = self.region_map[(r,c)]
            facts.append(f"region({r},{c},{rid}).")
        return facts

    def generate_game(self):
        self.clear_grid()
        if not CLINGO_AVAILABLE:
            messagebox.showerror("Error", "Librería 'clingo' no encontrada.")
            return

        rand_seed = str(random.randint(0, 32767))
        ctl = clingo.Control(arguments=["--sign-def=rnd", "--seed=" + rand_seed])
        ctl.configuration.solve.models = 1
        
        # INYECTAMOS EL TAMAÑO DINÁMICO (Generalización NxN)
        ctl.add("base", [], f"#const n={self.n}.")
        
        for (r,c), rid in self.region_map.items():
            ctl.add("base", [], f"region({r},{c},{rid}).")
            
        try:
            ctl.load("sudoku.lp")
        except:
            messagebox.showerror("Error", "Falta sudoku.lp")
            return

        ctl.ground([("base", [])])
        
        full_board = {}
        found = False
        with ctl.solve(yield_=True) as handle:
            for model in handle:
                found = True
                for atom in model.symbols(shown=True):
                    if atom.name == "cell":
                        full_board[(atom.arguments[0].number, atom.arguments[1].number)] = atom.arguments[2].number
        
        if not found:
            messagebox.showerror("Error", "No se pudo generar.")
            return

        self.full_solution = full_board

        # Ajuste de dificultad según el tamaño
        if self.n == 9:
            keep = 30 if self.difficulty.get() == "Medio" else (40 if self.difficulty.get() == "Fácil" else 24)
        else:
            # Para 4x4 (Total 16 celdas), dejamos poquitas ocultas
            keep = 6 if self.difficulty.get() == "Difícil" else (8 if self.difficulty.get() == "Medio" else 10)
        
        all_coords = list(full_board.keys())
        show_coords = random.sample(all_coords, keep)
        for coord in show_coords:
            self.cells[coord].insert(0, str(full_board[coord]))

    def solve_game(self, engine="clingo"):
        facts = self.get_facts()
        solution = []
        
        if engine == "clingo":
            if not CLINGO_AVAILABLE: return
            ctl = clingo.Control()
            ctl.configuration.solve.models = 1
            ctl.load("sudoku.lp")
            try:
                ctl.load("pure_logic.lp")
            except:
                print("Advertencia: strategy.lp no encontrado, resolviendo solo con fuerza bruta.")
            ctl.add("base", [], f"#const n={self.n}.") # Importante pasar n
            for f in facts: ctl.add("base", [], f)
            ctl.ground([("base", [])])
            with ctl.solve(yield_=True) as handle:
                for model in handle:
                    for atom in model.symbols(shown=True):
                        if atom.name == "cell":
                            solution.append((atom.arguments[0].number, atom.arguments[1].number, atom.arguments[2].number))
                            
        elif engine == "dlv":
            dlv_exe = "dlv.exe" if os.name == 'nt' else "./dlv"
            if not os.path.exists(dlv_exe):
                messagebox.showerror("Error", "Falta dlv.exe o no está en el PATH")
                return
            
            # 1. PREPARACIÓN DE HECHOS
            facts_for_dlv = self.get_facts()
            domain_facts = [f"val({i})." for i in range(1, self.n + 1)]
            facts_for_dlv.extend(domain_facts)
            
            with open("input_dlv.tmp", "w") as f: 
                f.write("\n".join(facts_for_dlv))
                
            # ============================================================
            #                 CONFIGURACIÓN DE ESTRATEGIAS
            # ============================================================
            
            PROBAR_SOLO_LOGICA = False  # Cambiar a True para modo científico
            
            cmd = [dlv_exe, "input_dlv.tmp"]
            
            if PROBAR_SOLO_LOGICA:
                # MODO CIENTIFICO: Solo usa 'solo_log.dl'
                # El resultado será parcial
                cmd.append("solo_log.dl")
            else:
                # MODO RESOLVER: Usa 'sudoku.dl' para llenar todo el tablero
                cmd.append("sudoku.dl")
                cmd.append("estrategias.dl")

            cmd.append("-filter=cell")
            
            # ============================================================

            try:
                res = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
                
                # PARSEO ROBUSTO CON REGEX
                pattern = r"cell\((\d+),(\d+),(\d+)\)"
                matches = re.findall(pattern, res.stdout)
                
                solution = []
                for (r, c, v) in matches:
                    solution.append((int(r), int(c), int(v)))
                
                if not solution and res.stderr:
                     print("DLV Output:", res.stdout)
                     messagebox.showerror("Posible Error DLV", res.stderr.strip())

            except subprocess.TimeoutExpired:
                 messagebox.showerror("Error DLV", "DLV tardó demasiado en responder.")
                 return
            except Exception as e:
                messagebox.showerror("Error DLV", f"Excepción: {str(e)}")

        for (r,c,v) in solution:
            if self.cells[(r,c)].get() == "":
                self.cells[(r,c)].insert(0, str(v))
                self.cells[(r,c)].config(fg="blue")

    def give_hint(self):
        if self.full_solution:
            empties = [coord for coord, entry in self.cells.items() if entry.get() == ""]
            if empties:
                target = random.choice(empties)
                self.cells[target].insert(0, str(self.full_solution[target]))
                self.cells[target].config(fg="green")
        else:
             self.solve_game("clingo")

    def clear_grid(self):
        self.full_solution = {}
        for e in self.cells.values():
            e.delete(0, tk.END)
            e.config(fg="black", bg=e.cget("bg"))

if __name__ == "__main__":
    root = tk.Tk()
    app = SudokuApp(root)
    root.mainloop()