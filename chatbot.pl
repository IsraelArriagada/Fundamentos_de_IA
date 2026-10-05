% =====================================================================
% CHATBOT EN PROLOG - Mitologia griega
% Uso interactivo:  swipl -q -g main -t halt prolog/chatbot.pl
% Uso por tuberia:  echo "quien es el padre de apolo" | swipl -q -g main -t halt prolog/chatbot.pl
% Flujo: texto -> tokens normalizados -> deteccion de entidades e intencion
%        -> consulta a la base kb.pl -> respuesta en espanol.
% =====================================================================
:- encoding(utf8).
:- use_module(library(lists)).
:- use_module(library(apply)).
:- use_module(library(readutil)).
:- consult(kb).     % se recarga en cada ejecucion: editar kb.pl basta

% ---------- 1. NORMALIZACION ----------
tokens(Texto, Tokens) :-
    string_lower(Texto, Min),
    string_codes(Min, Cs0),
    maplist(sin_tilde, Cs0, Cs1),
    maplist(solo_alnum, Cs1, Cs2),
    string_codes(S, Cs2),
    split_string(S, " ", " ", Partes),
    exclude(==(""), Partes, Ps),
    maplist([P,A]>>atom_string(A,P), Ps, Tokens).

sin_tilde(C, D) :- tilde(C, D), !.
sin_tilde(C, C).
tilde(0'á,0'a). tilde(0'é,0'e). tilde(0'í,0'i). tilde(0'ó,0'o).
tilde(0'ú,0'u). tilde(0'ü,0'u). tilde(0'ñ,0'n).

solo_alnum(C, C) :- code_type(C, alnum), !.
solo_alnum(0'_, 0'_) :- !.
solo_alnum(_, 0' ).

% ---------- 2. ENTIDADES ----------
% Un token es entidad si es un id de ficha/3 o un nombre romano (alias).
canon(T, T)  :- ficha(T,_,_), !.
canon(T, Id) :- romano(Id, N), tokens(N, [T]), !.

entidades(Tokens, Ids) :-
    findall(Id, (member(T, Tokens), canon(T, Id)), L0),
    dedup(L0, Ids).

dedup([], []).
dedup([X|Xs], [X|Ys]) :- exclude(==(X), Xs, Zs), dedup(Zs, Ys).

% ---------- 3. UTILIDADES DE SALIDA ----------
nombre(Id, N) :- ficha(Id, N, _), !.
nombre(Id, N) :- texto(Id, N).
texto(A, T) :- atomic_list_concat(Ps, '_', A), atomic_list_concat(Ps, ' ', T).

lista(Ids, Txt) :- maplist(nombre, Ids, Ns), unir(Ns, Txt).
unir([], ninguno) :- !.
unir([X], X) :- !.
unir([X,Y], T) :- !, format(atom(T), '~w y ~w', [X,Y]).
unir(L, T) :- append(I, [U], L), atomic_list_concat(I, ', ', IT), format(atom(T), '~w y ~w', [IT,U]).

lista_txt(As, Txt) :- maplist(texto, As, Ns), unir(Ns, Txt).

tiene(T, Palabras) :- member(P, Palabras), memberchk(P, T), !.
conjunto(Plantilla, Meta, L) :- findall(Plantilla, Meta, L0), sort(L0, L).

% Responde "Prefijo: lista." o el mensaje de vacio
resp_lista(_, [], Vacio, R) :- !, R = Vacio.
resp_lista(Fmt, Ids, _, R) :- lista(Ids, Txt), format(atom(R), Fmt, [Txt]).

% ---------- 4. INTENCIONES ----------
responder(Texto, Resp) :-
    tokens(Texto, T),
    entidades(T, Es),
    (   catch(intencion(T, Es, R), _, fail)
    ->  Resp = R
    ;   Resp = 'No pude responder esa pregunta con mi conocimiento. Escribe "ayuda" para ver ejemplos.'
    ).

% 4.1 Ayuda
intencion(T, _, R) :- tiene(T, [ayuda,hola,help]), !,
    R = 'Soy un chatbot de mitología griega. Prueba: "¿Quién es el padre de Apolo?", "¿Quiénes son los hermanos de Zeus?", "¿Quién es el dios del mar?", "¿Cuál es el símbolo de Atenea?", "¿Es Zeus hijo de Cronos?", "¿Quién mató a Medusa?", "¿Cómo se llama Zeus en Roma?".'.

% 4.2 Si/No sobre relaciones: "es A <relacion> de B"
intencion([V|T], [A,B|_], R) :- memberchk(V, [es,son,fue,era,esta,estan]),
    member(W, T), rel_palabra(W, Pred), !,
    G =.. [Pred, A, B], nombre(A, NA), nombre(B, NB),
    (   call(G)
    ->  ( Pred == casados -> format(atom(R), 'Sí, ~w y ~w están casados.', [NA,NB])
        ; format(atom(R), 'Sí, ~w es ~w de ~w.', [NA,W,NB]) )
    ;   ( Pred == casados -> format(atom(R), 'No, según mi conocimiento ~w y ~w no están casados.', [NA,NB])
        ; format(atom(R), 'No, según mi conocimiento ~w no es ~w de ~w.', [NA,W,NB]) )
    ).

% 4.3 Si/No sobre categoria: "es A olimpico / titan / heroe / dios ..."
intencion([V|T], [A|_], R) :- memberchk(V, [es,fue,era]),
    member(W, T), cat_palabra(W, Cat), !,
    nombre(A, NA),
    cat_etiqueta(Cat, W, Et),
    (   es_de_categoria(A, Cat) -> format(atom(R), 'Sí, ~w es ~w.', [NA,Et])
    ;   format(atom(R), 'No, según mi conocimiento ~w no es ~w.', [NA,Et]) ).

% 4.4 Familia
intencion(T, [E|_], R) :- tiene(T, [cuantos,cuantas]), tiene(T, [hijos,hijas,hijo,hija]), !,
    conjunto(H, progenitor(E,H), L), length(L, N), nombre(E, NE), lista(L, Txt),
    format(atom(R), '~w tiene ~d hijos registrados: ~w.', [NE,N,Txt]).
intencion(T, [E|_], R) :- tiene(T, [padres]), !,
    conjunto(P, progenitor(P,E), L), nombre(E, NE),
    format(atom(Vacio), 'No tengo registrados los padres de ~w.', [NE]),
    resp_lista('Los padres son: ~w.', L, Vacio, R).
intencion(T, [E|_], R) :- tiene(T, [padre]), !,
    conjunto(P, padre(P,E), L), nombre(E, NE),
    format(atom(Vacio), 'No tengo registrado el padre de ~w.', [NE]),
    resp_lista('El padre es ~w.', L, Vacio, R).
intencion(T, [E|_], R) :- tiene(T, [madre]), !,
    conjunto(M, madre(M,E), L), nombre(E, NE),
    format(atom(Vacio), 'No tengo registrada la madre de ~w.', [NE]),
    resp_lista('La madre es ~w.', L, Vacio, R).
intencion(T, [E|_], R) :- tiene(T, [hijos,hijas,hijo,hija]), !,
    conjunto(H, progenitor(E,H), L), nombre(E, NE),
    format(atom(Vacio), 'No tengo registrados hijos de ~w.', [NE]),
    resp_lista('Los hijos son: ~w.', L, Vacio, R).
intencion(T, [E|_], R) :- tiene(T, [hermanos,hermanas,hermano,hermana]), !,
    conjunto(X, hermano(X,E), L), nombre(E, NE),
    format(atom(Vacio), 'No tengo registrados hermanos de ~w.', [NE]),
    resp_lista('Los hermanos (comparten al menos un progenitor) son: ~w.', L, Vacio, R).
intencion(T, [E|_], R) :- tiene(T, [abuelos,abuelo,abuela]), !,
    conjunto(X, abuelo(X,E), L), nombre(E, NE),
    format(atom(Vacio), 'No tengo registrados abuelos de ~w.', [NE]),
    resp_lista('Los abuelos son: ~w.', L, Vacio, R).
intencion(T, [E|_], R) :- tiene(T, [tios,tio,tia,tias]), !,
    conjunto(X, tio(X,E), L), nombre(E, NE),
    format(atom(Vacio), 'No tengo registrados tíos de ~w.', [NE]),
    resp_lista('Los tíos son: ~w.', L, Vacio, R).
intencion(T, [E|_], R) :- tiene(T, [descendientes,descendencia]), !,
    conjunto(X, descendiente(X,E), L), nombre(E, NE),
    format(atom(Vacio), 'No tengo registrados descendientes de ~w.', [NE]),
    resp_lista('Los descendientes son: ~w.', L, Vacio, R).
intencion(T, [E|_], R) :- tiene(T, [ancestros,antepasados]), !,
    conjunto(X, descendiente(E,X), L), nombre(E, NE),
    format(atom(Vacio), 'No tengo registrados ancestros de ~w.', [NE]),
    resp_lista('Los ancestros son: ~w.', L, Vacio, R).
intencion(T, [E|_], R) :- tiene(T, [esposo,esposa,pareja,casado,casada,marido,conyuge]), !,
    conjunto(X, casados(E,X), L), nombre(E, NE),
    format(atom(Vacio), 'No tengo registrada una pareja de ~w.', [NE]),
    resp_lista('La pareja es ~w.', L, Vacio, R).

% 4.5 Atributos
intencion(T, [E|_], R) :- tiene(T, [simbolo,simbolos,atributos,emblema]), !,
    conjunto(S, simbolo(E,S), L), nombre(E, NE),
    ( L == [] -> format(atom(R), 'No tengo registrados símbolos de ~w.', [NE])
    ; lista_txt(L, Txt), format(atom(R), 'Los símbolos de ~w son: ~w.', [NE,Txt]) ).
intencion(T, [E|_], R) :- tiene(T, [romano,romana,roma,latino]), !,
    nombre(E, NE),
    ( romano(E, N) -> format(atom(R), '~w se llama ~w en la mitología romana.', [NE,N])
    ; format(atom(R), 'No tengo registrado un equivalente romano de ~w.', [NE]) ).
intencion(T, [E|_], R) :- tiene(T, [vive,viven,reside,habita,donde]), !,
    nombre(E, NE),
    ( residencia(E, L) -> format(atom(R), '~w vive en ~w.', [NE,L])
    ; format(atom(R), 'No tengo registrado dónde vive ~w.', [NE]) ).

% 4.6 Heroes y criaturas
intencion(T, [E|_], R) :- tiene(T, [mato,derroto,vencio,asesino,mataron]), categoria(E, criatura), !,
    conjunto(X, mato(X,E), L), nombre(E, NE),
    format(atom(Vacio), 'No tengo registrado quién derrotó a ~w.', [NE]),
    resp_lista('Fue derrotado por: ~w.', L, Vacio, R).
intencion(T, [E|_], R) :- tiene(T, [mato,derroto,vencio,asesino,mataron]), !,
    conjunto(X, mato(E,X), L), nombre(E, NE),
    format(atom(Vacio), 'No tengo registradas criaturas derrotadas por ~w.', [NE]),
    resp_lista('Derrotó a: ~w.', L, Vacio, R).
intencion(T, [E|_], R) :- tiene(T, [hazanas,hazana,proezas,trabajos,hizo,logro,logros]), !,
    conjunto(H, hazana(E,H), L), nombre(E, NE),
    ( L == [] -> format(atom(R), 'No tengo hazañas registradas de ~w.', [NE])
    ; atomic_list_concat(L, '; ', Txt), format(atom(R), '~w ~w.', [NE,Txt]) ).

% 4.7 Dominio de una divinidad: "de que es dios Apolo"
intencion(T, [E|_], R) :- tiene(T, [dominio,dominios,dios,diosa,patron,patrono]),
    \+ tiene(T, [quien,quienes]), !,
    conjunto(D, dominio(E,D), L), nombre(E, NE),
    ( L == [] -> format(atom(R), 'No tengo registrados dominios de ~w.', [NE])
    ; lista_txt(L, Txt), format(atom(R), '~w es divinidad de: ~w.', [NE,Txt]) ).

% 4.8 Busqueda inversa por dominio: "quien es el dios del mar"
intencion(T, [], R) :- member(Tok, T), dominio(_, D), tokens(D, [Tok]), !,
    conjunto(Id, dominio(Id,D), L), lista(L, Txt), texto(D, DT),
    format(atom(R), 'La divinidad asociada a «~w» es: ~w.', [DT,Txt]).

% 4.9 Listados por categoria
intencion(T, [], R) :- member(W, T), cat_plural(W, Cat, Etiqueta), !,
    conjunto(Id, categoria(Id,Cat), L), lista(L, Txt),
    format(atom(R), '~w: ~w.', [Etiqueta,Txt]).

% 4.10 Ficha general: "quien es X"
intencion(_, [E|_], R) :- !, ficha_texto(E, R).

% ---------- 5. TABLAS DE VOCABULARIO ----------
rel_palabra(padre,padre).     rel_palabra(madre,madre).
rel_palabra(hijo,hijo).       rel_palabra(hija,hijo).
rel_palabra(hermano,hermano). rel_palabra(hermana,hermano).
rel_palabra(abuelo,abuelo).   rel_palabra(abuela,abuelo).
rel_palabra(tio,tio).         rel_palabra(tia,tio).
rel_palabra(descendiente,descendiente).
rel_palabra(esposo,casados).  rel_palabra(esposa,casados).
rel_palabra(casado,casados).  rel_palabra(casados,casados).
rel_palabra(pareja,casados).  rel_palabra(marido,casados).
rel_palabra(hermanos,hermano). rel_palabra(hermanas,hermano).

cat_palabra(olimpico,olimpico). cat_palabra(olimpica,olimpico).
cat_palabra(titan,titan).       cat_palabra(titanide,titan).
cat_palabra(heroe,heroe).       cat_palabra(semidios,semidios).
cat_palabra(mortal,mortal).     cat_palabra(primordial,primordial).
cat_palabra(criatura,criatura). cat_palabra(monstruo,criatura).
cat_palabra(dios,divino).       cat_palabra(diosa,divino_f).

cat_etiqueta(Cat, _, Et) :- cat_texto(Cat, Et), !.
cat_etiqueta(_, W, W).

es_de_categoria(A, divino)   :- !, categoria(A, C), memberchk(C, [olimpico,dios_menor,titan,primordial]), ficha(A,_,m).
es_de_categoria(A, divino_f) :- !, categoria(A, C), memberchk(C, [olimpico,dios_menor,titan,primordial]), ficha(A,_,f).
es_de_categoria(A, Cat)      :- categoria(A, Cat).

cat_plural(olimpicos,olimpico,'Los dioses olímpicos registrados son').
cat_plural(olimpicas,olimpico,'Los dioses olímpicos registrados son').
cat_plural(titanes,titan,'Los titanes registrados son').
cat_plural(heroes,heroe,'Los héroes registrados son').
cat_plural(semidioses,semidios,'Los semidioses registrados son').
cat_plural(primordiales,primordial,'Las divinidades primordiales son').
cat_plural(monstruos,criatura,'Las criaturas registradas son').
cat_plural(criaturas,criatura,'Las criaturas registradas son').
cat_plural(dioses,olimpico,'Los dioses olímpicos registrados son').

cat_texto(primordial,'divinidad primordial'). cat_texto(titan,'titán').
cat_texto(olimpico,'divinidad olímpica').     cat_texto(dios_menor,'divinidad menor').
cat_texto(semidios,'semidiós').               cat_texto(heroe,'héroe').
cat_texto(mortal,'mortal').                   cat_texto(ninfa,'ninfa').
cat_texto(nereida,'nereida').                 cat_texto(criatura,'criatura mitológica').

% ---------- 6. FICHA GENERAL ----------
ficha_texto(E, R) :-
    nombre(E, NE),
    conjunto(C, categoria(E,C), Cs),
    findall(Tx, (member(C0,Cs), cat_texto(C0,Tx)), Ts),
    ( Ts == [] -> P1 = '' ; unir(Ts, TT), format(atom(P1), '~w es ~w. ', [NE,TT]) ),
    conjunto(D, dominio(E,D), Ds),
    ( Ds == [] -> P2 = '' ; lista_txt(Ds, DT), format(atom(P2), 'Dominios: ~w. ', [DT]) ),
    conjunto(S, simbolo(E,S), Ss),
    ( Ss == [] -> P3 = '' ; lista_txt(Ss, ST), format(atom(P3), 'Símbolos: ~w. ', [ST]) ),
    conjunto(P, progenitor(P,E), Ps),
    ( Ps == [] -> P4 = '' ; lista(Ps, PT), format(atom(P4), 'Hijo/a de ~w. ', [PT]) ),
    ( romano(E, N) -> format(atom(P5), 'Equivalente romano: ~w.', [N]) ; P5 = '' ),
    atomic_list_concat([P1,P2,P3,P4,P5], R0),
    ( R0 == '' -> format(atom(R), 'Conozco a ~w, pero tengo pocos datos.', [NE]) ; normalize_space(atom(R), R0) ).

% ---------- 7. BUCLE PRINCIPAL ----------
main :-
    set_stream(user_input, encoding(utf8)),
    set_stream(user_output, encoding(utf8)),
    (   stream_property(user_input, tty(true))
    ->  format("Chatbot de Mitología Griega. Escribe 'ayuda' o 'salir'.~n"), Prompt = true
    ;   Prompt = false ),
    bucle(Prompt).

bucle(P) :-
    ( P == true -> format("> "), flush_output ; true ),
    read_line_to_string(user_input, L),
    (   L == end_of_file -> true
    ;   split_string(L, "", " \t\r\n", [Tr]),
        (   memberchk(Tr, ["salir","exit","chao"]) -> true
        ;   Tr == "" -> bucle(P)
        ;   responder(Tr, R), format("~w~n", [R]), flush_output, bucle(P)
        )
    ).
