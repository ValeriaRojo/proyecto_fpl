% --- pure_logic.lp (TODO TERRENO) ---
val(1..n).

% 1. Celdas ya conocidas (Iniciales + lo que ya hayamos resuelto en iteraciones previas si hubiera)
known(R, C, V) :- inicial(R, C, V).

% 2. Definir Candidatos: ¿Qué valores PUEDEN ir en (R,C)?
candidate(R, C, V) :- 
    val(R), val(C), val(V),
    not known(R, C, _),             % La celda debe estar vacía
    not known(R, _, V),             % No está en la fila
    not known(_, C, V),             % No está en la columna
    not region_conflict(R, C, V).   % No está en la región

% Conflicto de región
region_conflict(R, C, V) :- 
    region(R, C, ID), region(R2, C2, ID), 
    known(R2, C2, V), (R,C) != (R2,C2).

% --------------------------------------------------------
% ESTRATEGIA 1: NAKED SINGLE (La más básica)
% Si una celda solo tiene 1 candidato, ¡ese es el valor!
% --------------------------------------------------------
% Contamos cuántos candidatos tiene cada celda usando sintaxis segura
count_cand(R, C, N) :- 
    val(R), val(C), not known(R, C, _),
    N = { candidate(R, C, V) : val(V) }. 

% Si N=1, es un Naked Single
found(R, C, V) :-
    count_cand(R, C, 1),
    candidate(R, C, V).

% --------------------------------------------------------
% ESTRATEGIA 2: NAKED PAIRS (Tu objetivo)
% --------------------------------------------------------
% Detectar celdas con exactamente 2 candidatos
pair_cell(R, C) :- count_cand(R, C, 2).

% Detectar el par en la misma FILA
naked_pair_row(R, C1, C2) :-
    val(R), val(C1), val(C2), C1 < C2,
    pair_cell(R, C1), pair_cell(R, C2),
    % Verificamos que tengan EXACTAMENTE los mismos candidatos
    candidate(R, C1, V) : candidate(R, C2, V);
    candidate(R, C2, V) : candidate(R, C1, V).

% Identificar los valores de ese par para eliminarlos de otros lados
pair_values(R, C1, C2, V) :-
    naked_pair_row(R, C1, C2),
    candidate(R, C1, V).

% REGLA DE ELIMINACIÓN:
% Un candidato deja de ser válido si choca con un Naked Pair
eliminated(R, C3, V) :-
    pair_values(R, C1, C2, V), % V es parte de un par en (C1, C2)
    val(C3), C3 != C1, C3 != C2, % C3 es otra celda en la misma fila
    candidate(R, C3, V).         % Y C3 tenía a V como candidato

% --------------------------------------------------------
% ESTRATEGIA 3: POINTING PAIRS (Intersección Bloque-Línea)
% --------------------------------------------------------
% Definición: Si en un bloque (región), todos los candidatos de un número V
% están alineados en la misma fila R, entonces ese número V NO puede estar
% en esa fila R fuera de ese bloque.

% 1. Detectar si un numero V en un bloque ID solo aparece en una fila R
block_row_claim(ID, R, V) :-
    val(ID), val(R), val(V),
    % Existe al menos un candidato V en esa fila dentro del bloque
    candidate(R, C, V), region(R, C, ID),
    % Y NO existe ningún candidato V en ese bloque que NO sea de esa fila
    not candidate_outside_row_in_block(ID, R, V).

% Auxiliar: ¿Hay un candidato V en el bloque ID que NO esté en la fila R?
candidate_outside_row_in_block(ID, R, V) :-
    val(ID), val(R), val(V),
    candidate(R2, C2, V), 
    region(R2, C2, ID),
    R2 != R.

% 2. ELIMINAR: Si el bloque reclama la fila, borramos V del resto de la fila
eliminated(R, C, V) :-
    block_row_claim(ID, R, V),  % El bloque ID reclama al valor V en la fila R
    candidate(R, C, V),         % Hay un candidato V en esa fila
    not region(R, C, ID).       % Pero está FUERA del bloque que reclama

% (Lo mismo para COLUMNAS - Pointing Pairs Vertical)
block_col_claim(ID, C, V) :-
    val(ID), val(C), val(V),
    candidate(R, C, V), region(R, C, ID),
    not candidate_outside_col_in_block(ID, C, V).

candidate_outside_col_in_block(ID, C, V) :-
    val(ID), val(C), val(V),
    candidate(R2, C2, V), 
    region(R2, C2, ID),
    C2 != C.

eliminated(R, C, V) :-
    block_col_claim(ID, C, V),
    candidate(R, C, V),
    not region(R, C, ID).

% --------------------------------------------------------
% SALIDA FINAL
% --------------------------------------------------------

% Solo mostramos lo que hemos ENCONTRADO nuevo en esta pasada
#show cell(R,C,V) : found(R,C,V).

% DEBUG: Si no sale nada arriba, descomenta esto para ver si al menos detecta candidatos
% #show candidate/3.
% #show naked_pair_row/3.