% --- Reglas de Sudoku para Clingo ---
% Este archivo define la lógica. El tamaño 'n' se pasa desde Python.

#const n=3.
#const s=n*n.

% --- Dominios ---
val(1..s).
row(0..s-1).
col(0..s-1).

% --- Generador ---
% Para cada celda (R,C) que NO está dada (given), asigna un valor V.
1 { sudoku(R, C, V) : val(V) } 1 :- row(R), col(C), not given(R, C).

% Definir qué es 'given' basado en la entrada (para simplificar reglas abajo)
given(R, C) :- sudoku(R, C, V), given_input(R, C, V).
sudoku(R, C, V) :- given_input(R, C, V).

% --- Restricciones ---

% 1. Fila única: En una fila R, un valor V no puede aparecer más de una vez.
:- row(R), val(V), not 1 { sudoku(R, C, V) : col(C) } 1.

% 2. Columna única: En una columna C, un valor V no puede aparecer más de una vez.
:- col(C), val(V), not 1 { sudoku(R, C, V) : row(R) } 1.

% 3. Bloque único:
:- val(V), BR = 0..n-1, BC = 0..n-1,
   not 1 { sudoku(R, C, V) : row(R), col(C), R/n == BR, C/n == BC } 1.

% --- Salida ---
#show sudoku/3.