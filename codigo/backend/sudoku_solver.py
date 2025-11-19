import subprocess
import os
import random
import re
from typing import List, Optional, Tuple

# Tipos de datos para ayudar al autocompletado
Grid = List[List[int]]

# Nombres de los ejecutables (ASEGÚRATE DE TENERLOS EN TU PATH O CARPETA)
CLINGO_EXEC = "C:/Users/Valeria Rojo/Downloads/clingo-4.5.4-win64/clingo-4.5.4-win64/clingo.exe" # O la ruta a tu ejecutable clingo (ej: ./clingo.bin)
DLV_EXEC = "C:/Users/Valeria Rojo/Desktop/dlv.mingw"       # O la ruta a tu ejecutable dlv (ej: ./dlv.bin)

# Archivos de reglas
CLINGO_FILE = "sudoku_clingo.lp"
DLV_FILE = "sudoku_dlv.dl"

def parse_output(output: str) -> Optional[Grid]:
    """
    Parsea la salida de texto de Clingo/DLV y la convierte en una matriz de Python.
    Busca predicados sudoku(R,C,V).
    """
    # Buscar todos los sudoku(r,c,v) usando expresiones regulares
    matches = re.findall(r'sudoku\((\d+),(\d+),(\d+)\)', output)
    
    if not matches:
        return None

    # Determinar tamaño basado en el índice más grande encontrado
    max_idx = 0
    for r, c, v in matches:
        max_idx = max(max_idx, int(r), int(c))
    
    size = max_idx + 1
    grid = [[0 for _ in range(size)] for _ in range(size)]

    for r, c, v in matches:
        grid[int(r)][int(c)] = int(v)
    
    return grid

def grid_to_facts(grid: Grid) -> str:
    """Convierte la matriz Python a hechos ASP: given_input(r,c,v)."""
    facts = ""
    for r in range(len(grid)):
        for c in range(len(grid[r])):
            if grid[r][c] != 0:
                facts += f"given_input({r},{c},{grid[r][c]}). "
    return facts

def solve_with_clingo(grid: Grid, n: int, s: int) -> Optional[Grid]:
    """Llama al ejecutable de Clingo."""
    facts = grid_to_facts(grid)
    
    # Pasamos el tamaño 'n' como constante desde línea de comandos
    cmd = [CLINGO_EXEC, CLINGO_FILE, "--const", f"n={n}", "0"]
    
    try:
        # Ejecutar proceso enviando los hechos por stdin
        process = subprocess.Popen(
            cmd, 
            stdin=subprocess.PIPE, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            text=True
        )
        stdout, stderr = process.communicate(input=facts)
        
        if stderr:
            print(f"Clingo Stderr: {stderr}")
            
        return parse_output(stdout)
    except FileNotFoundError:
        raise Exception("No se encontró el ejecutable 'clingo'. Asegúrate de instalarlo.")

def solve_with_dlv(grid: Grid, n: int, s: int) -> Optional[Grid]:
    """Llama al ejecutable de DLV."""
    facts = grid_to_facts(grid)
    
    # Nota: DLV maneja constantes diferente. A veces es mejor inyectarlas como texto.
    # Opción A: Pasar hechos y reglas todo junto por stdin
    # Opción B: Usar argumentos de DLV. Usaremos stdin para máxima compatibilidad.
    
    const_def = f"#const n={n}. "
    
    # Leemos el archivo de reglas para enviarlo junto con los datos
    with open(DLV_FILE, 'r') as f:
        rules = f.read()
    
    full_input = const_def + rules + "\n" + facts
    
    try:
        process = subprocess.Popen(
            [DLV_EXEC, "--silent"], # --silent limpia la salida en algunas versiones
            stdin=subprocess.PIPE, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            text=True
        )
        stdout, stderr = process.communicate(input=full_input)
        
        # DLV a veces pone warnings en stderr, no siempre es error fatal
        return parse_output(stdout)
    except FileNotFoundError:
        raise Exception("No se encontró el ejecutable 'dlv'.")

def generate_solved_grid(n: int, s: int) -> Optional[Grid]:
    """
    Genera un tablero completo válido llamando a Clingo con 0 restricciones de entrada.
    Usa argumentos aleatorios de Clingo para variedad.
    """
    # --sign-def=3 y --seed aleatorio ayuda a generar soluciones distintas
    seed = random.randint(1, 30000)
    cmd = [CLINGO_EXEC, CLINGO_FILE, "--const", f"n={n}", "1", "--sign-def=3", f"--seed={seed}"]
    
    try:
        process = subprocess.Popen(
            cmd, 
            stdin=subprocess.PIPE, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE, 
            text=True
        )
        # Enviamos entrada vacía (sin given_input)
        stdout, stderr = process.communicate(input="")
        return parse_output(stdout)
    except Exception as e:
        print(f"Error generando grid: {e}")
        return None

def create_puzzle(full_grid: Grid, s: int, difficulty: float) -> Grid:
    """
    Toma un grid completo y elimina números basado en la dificultad.
    difficulty: Porcentaje de celdas a eliminar (0.4 a 0.7 aprox).
    """
    puzzle = [row[:] for row in full_grid] # Copia profunda
    total_cells = s * s
    to_remove = int(total_cells * difficulty)
    
    positions = [(r, c) for r in range(s) for c in range(s)]
    random.shuffle(positions)
    
    for i in range(to_remove):
        r, c = positions[i]
        puzzle[r][c] = 0
        
    return puzzle