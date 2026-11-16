% =====================================================================
% EXPORTADOR DE LA BASE DE CONOCIMIENTO PARA EL CHATBOT LLM
% Uso: swipl -q -g exportar -t halt prolog/exportar.pl
% Escribe una ficha en texto por cada entidad de kb.pl, con SOLO los hechos
% directos (sin aplicar reglas), para que el LLM razone sobre ellos.
% Asi ambos chatbots usan exactamente el mismo conocimiento.
% =====================================================================
:- encoding(utf8).
:- prolog_load_context(directory, Dir), atom_concat(Dir, '/kb.pl', Kb), consult(Kb).

exportar :-
    set_stream(user_output, encoding(utf8)),
    forall(ficha(Id, Nombre, G), perfil(Id, Nombre, G)).

perfil(Id, Nombre, G) :-
    ( G == f -> Gen = femenino ; Gen = masculino ),
    format("- ~w (género ~w)", [Nombre, Gen]),
    campo('categorías',     X, categoria(Id, X)),
    campo('padres',         X, progenitor(X, Id)),
    campo('hijos',          X, progenitor(Id, X)),
    campo('pareja',         X, (pareja(Id, X) ; pareja(X, Id))),
    campo('dominios',       X, dominio(Id, X)),
    campo('símbolos',       X, simbolo(Id, X)),
    campo('vive en',        X, residencia(Id, X)),
    campo('nombre romano',  X, romano(Id, X)),
    campo('derrotó a',      X, mato(Id, X)),
    campo('derrotado/a por', X, mato(X, Id)),
    campo('hazañas',        X, hazana(Id, X)),
    campo('descripción',    X, descripcion(Id, X)),
    nl.

% campo(+Etiqueta, ?X, +Meta): imprime " | etiqueta: a, b" si Meta tiene soluciones
campo(Etiqueta, X, Meta) :-
    findall(X, Meta, L0), sort(L0, L),
    (   L == [] -> true
    ;   maplist(legible, L, Ns), atomic_list_concat(Ns, ', ', Txt),
        format(" | ~w: ~w", [Etiqueta, Txt])
    ).

legible(A, N) :- ficha(A, N, _), !.
legible(A, N) :- atomic_list_concat(Ps, '_', A), atomic_list_concat(Ps, ' ', N).
