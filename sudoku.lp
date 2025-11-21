% --- sudoku.lp ---
% ESTE ARCHIVO SIRVE PARA CLINGO Y PARA DLV

% Definimos valores del 1 al N (N se define desde Python)
val(1..n).

% 1. Cada celda (X,Y) debe tener exactamente un número V.
% Sintaxis compatible:
1 { cell(X,Y,V) : val(V) } 1 :- val(X), val(Y).

% 2. Restricción de Fila: No repetir número en la misma fila X.
:- cell(X,Y1,V), cell(X,Y2,V), Y1 != Y2.

% 3. Restricción de Columna: No repetir número en la misma columna Y.
:- cell(X1,Y,V), cell(X2,Y,V), X1 != X2.

% 4. Restricción de REGIÓN (La clave para el Sudoku Irregular):
% Si dos celdas tienen el mismo ID de región 'R', no pueden tener el mismo valor.
:- cell(X,Y,V), cell(A,B,V), region(X,Y,R), region(A,B,R), (X,Y) != (A,B).

% 5. Respetar los números iniciales (Pistas que pone el usuario).
:- inicial(X,Y,V), not cell(X,Y,V).

% Mostrar solo la solución final
#show cell/3.