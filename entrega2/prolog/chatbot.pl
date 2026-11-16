% =====================================================================
% CHATBOT EN PROLOG - Mitologia griega
% Uso interactivo:  swipl -q -g main -t halt prolog/chatbot.pl
% Uso por tuberia:  echo "quien es el padre de apolo" | swipl -q -g main -t halt prolog/chatbot.pl
% Flujo: texto -> tokens normalizados (sin tildes, sinonimos) -> deteccion
%        de entidades e intencion -> consulta a kb.pl -> respuesta en espanol.
% =====================================================================
:- encoding(utf8).
:- use_module(library(lists)).
:- use_module(library(apply)).
:- use_module(library(readutil)).

% ---------- 0. CARGA Y RECARGA DE LA BASE DE CONOCIMIENTO ----------
% kb.pl se vuelve a cargar automaticamente si se modifico desde la ultima
% pregunta, asi el conocimiento puede editarse sin reiniciar el chatbot.
:- dynamic kb_ruta/1, kb_fecha/1.
:- prolog_load_context(directory, Dir),
   atom_concat(Dir, '/kb.pl', Ruta),
   retractall(kb_ruta(_)), assertz(kb_ruta(Ruta)).

cargar_kb :-
    kb_ruta(Ruta),
    consult(Ruta),
    time_file(Ruta, Fecha),
    retractall(kb_fecha(_)), assertz(kb_fecha(Fecha)).

recargar_kb_si_cambio :-
    kb_ruta(Ruta), time_file(Ruta, Fecha),
    (   kb_fecha(Anterior), Fecha =:= Anterior
    ->  true
    ;   cargar_kb
    ).

:- cargar_kb.

% ---------- 1. NORMALIZACION ----------
tokens(Texto, Tokens) :-
    string_lower(Texto, Min),
    string_codes(Min, Cs0),
    maplist(sin_tilde, Cs0, Cs1),
    maplist(solo_alnum, Cs1, Cs2),
    string_codes(S, Cs2),
    split_string(S, " ", " ", Partes),
    exclude(==(""), Partes, Ps),
    maplist([P,A]>>atom_string(A,P), Ps, Tokens0),
    maplist(sinonimo_o_igual, Tokens0, Tokens).

sin_tilde(C, D) :- tilde(C, D), !.
sin_tilde(C, C).
tilde(0'á,0'a). tilde(0'é,0'e). tilde(0'í,0'i). tilde(0'ó,0'o).
tilde(0'ú,0'u). tilde(0'ü,0'u). tilde(0'ñ,0'n).

solo_alnum(C, C) :- code_type(C, alnum), !.
solo_alnum(0'_, 0'_) :- !.
solo_alnum(_, 0' ).

% Sinonimos coloquiales -> palabra que entiende el chatbot
sinonimo_o_igual(T, S) :- sinonimo(T, S), !.
sinonimo_o_igual(T, T).
sinonimo(mama, madre).        sinonimo(mami, madre).
sinonimo(papa, padre).        sinonimo(papi, padre).
sinonimo(progenitores, padres). sinonimo(engendro, padre).
sinonimo(hermanastro, hermano). sinonimo(hermanastra, hermana).
sinonimo(asesinaron, mato).   sinonimo(mataron, mato).
sinonimo(derrotaron, derroto). sinonimo(vencieron, vencio).
sinonimo(emblemas, simbolos). sinonimo(atributo, simbolo).

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

% Terminacion segun genero: o (masculino) / a (femenino)
gen(Id, a) :- ficha(Id, _, f), !.
gen(_, o).

lista(Ids, Txt) :- maplist(nombre, Ids, Ns), unir(Ns, Txt).
unir([], ninguno) :- !.
unir([X], X) :- !.
unir([X,Y], T) :- !, format(atom(T), '~w y ~w', [X,Y]).
unir(L, T) :- append(I, [U], L), atomic_list_concat(I, ', ', IT), format(atom(T), '~w y ~w', [IT,U]).

lista_txt(As, Txt) :- maplist(nombre, As, Ns), unir(Ns, Txt).

tiene(T, Palabras) :- member(P, Palabras), memberchk(P, T), !.
conjunto(Plantilla, Meta, L) :- findall(Plantilla, Meta, L0), sort(L0, L).

% resp_lista(+Prefijo, +Ids, +MensajeVacio, -Respuesta)
% Responde "Prefijo lista." o el mensaje de vacio.
resp_lista(_, [], Vacio, R) :- !, R = Vacio.
resp_lista(Prefijo, Ids, _, R) :- lista(Ids, Txt), format(atom(R), '~w~w.', [Prefijo,Txt]).

% Hijos de una entidad, o hijos en comun si se nombran dos ("hijos de Zeus y Hera")
hijos_de([A,B|_], L, Quien) :- !,
    conjunto(H, (progenitor(A,H), progenitor(B,H)), L),
    nombre(A, NA), nombre(B, NB), format(atom(Quien), '~w y ~w', [NA,NB]).
hijos_de([A|_], L, Quien) :-
    conjunto(H, progenitor(A,H), L), nombre(A, Quien).

% ---------- 4. INTENCIONES ----------
responder(Texto, Resp) :-
    tokens(Texto, T),
    entidades(T, Es),
    (   catch(intencion(T, Es, R), Error, (print_message(error, Error), fail))
    ->  capitalizar(R, Resp)
    ;   Resp = 'No pude responder esa pregunta con mi conocimiento. Escribe "ayuda" para ver ejemplos.'
    ).

% Pregunta de si/no: empieza con el verbo ("es A ...") o con la entidad ("A es ...")
verbo_sino(V) :- memberchk(V, [es,son,fue,era,esta,estan]).
pregunta_sino([V|T], T)    :- verbo_sino(V), !.
pregunta_sino([E,V|T], T)  :- canon(E, _), verbo_sino(V).

capitalizar(R, C) :-
    sub_atom(R, 0, 1, _, F), upcase_atom(F, FU),
    sub_atom(R, 1, _, 0, Resto), atom_concat(FU, Resto, C).

% 4.1 Ayuda
intencion(T, _, R) :- tiene(T, [ayuda,hola,help]), !,
    R = 'Soy un chatbot de mitología griega. Prueba: "¿Quién es el padre de Apolo?", "¿Quiénes son los hermanos de Zeus?", "¿Quién es el dios del mar?", "¿Cuál es el símbolo de Atenea?", "¿Es Zeus hijo de Cronos?", "¿Quién mató a Medusa?", "¿Cómo se llama Zeus en Roma?".'.

% 4.2 Si/No sobre relaciones: "es A <relacion> de B"
intencion(T0, [A,B|_], R) :- pregunta_sino(T0, T),
    member(W, T), rel_palabra(W, Pred), !,
    G =.. [Pred, A, B], nombre(A, NA), nombre(B, NB),
    rel_texto(Pred, A, Rel),
    (   call(G)
    ->  ( Pred == casados -> format(atom(R), 'Sí, ~w y ~w están casados.', [NA,NB])
        ; format(atom(R), 'Sí, ~w es ~w de ~w.', [NA,Rel,NB]) )
    ;   ( Pred == casados -> format(atom(R), 'No, según mi conocimiento ~w y ~w no están casados.', [NA,NB])
        ; format(atom(R), 'No, según mi conocimiento ~w no es ~w de ~w.', [NA,Rel,NB]) )
    ).

% 4.3 Si/No sobre categoria: "es A olimpico / titan / heroe / dios ..."
intencion(T0, [A|_], R) :- pregunta_sino(T0, T),
    member(W, T), cat_palabra(W, Cat), !,
    nombre(A, NA),
    cat_etiqueta(Cat, W, Et),
    (   es_de_categoria(A, Cat) -> format(atom(R), 'Sí, ~w es ~w.', [NA,Et])
    ;   format(atom(R), 'No, según mi conocimiento ~w no es ~w.', [NA,Et]) ).

% 4.4 Familia
intencion(T, Es, R) :- Es = [_|_], tiene(T, [cuantos,cuantas]), tiene(T, [hijos,hijas,hijo,hija]), !,
    hijos_de(Es, L, Quien), length(L, N), lista(L, Txt),
    ( Es = [_,_|_] -> Verbo = tienen ; Verbo = tiene ),
    format(atom(R), '~w ~w ~d hijos registrados: ~w.', [Quien,Verbo,N,Txt]).
intencion(T, [E|_], R) :- tiene(T, [padres]), !,
    conjunto(P, progenitor(P,E), L), nombre(E, NE),
    format(atom(Vacio), 'No tengo registrados los padres de ~w.', [NE]),
    format(atom(Pref), 'Los padres de ~w son: ', [NE]),
    resp_lista(Pref, L, Vacio, R).
intencion(T, [E|_], R) :- tiene(T, [padre]), !,
    conjunto(P, padre(P,E), L), nombre(E, NE),
    format(atom(Vacio), 'No tengo registrado el padre de ~w.', [NE]),
    format(atom(Pref), 'El padre de ~w es ', [NE]),
    resp_lista(Pref, L, Vacio, R).
intencion(T, [E|_], R) :- tiene(T, [madre]), !,
    conjunto(M, madre(M,E), L), nombre(E, NE),
    format(atom(Vacio), 'No tengo registrada la madre de ~w.', [NE]),
    format(atom(Pref), 'La madre de ~w es ', [NE]),
    resp_lista(Pref, L, Vacio, R).
intencion(T, Es, R) :- Es = [_|_], tiene(T, [hijos,hijas,hijo,hija]), !,
    hijos_de(Es, L, Quien),
    format(atom(Vacio), 'No tengo registrados hijos de ~w.', [Quien]),
    format(atom(Pref), 'Los hijos de ~w son: ', [Quien]),
    resp_lista(Pref, L, Vacio, R).
intencion(T, [E|_], R) :- tiene(T, [hermanos,hermanas,hermano,hermana]), !,
    conjunto(X, hermano(X,E), L), nombre(E, NE),
    format(atom(Vacio), 'No tengo registrados hermanos de ~w.', [NE]),
    format(atom(Pref), 'Los hermanos de ~w (comparten al menos un progenitor) son: ', [NE]),
    resp_lista(Pref, L, Vacio, R).
intencion(T, [E|_], R) :- tiene(T, [abuelos,abuelo,abuela]), !,
    conjunto(X, abuelo(X,E), L), nombre(E, NE),
    format(atom(Vacio), 'No tengo registrados abuelos de ~w.', [NE]),
    format(atom(Pref), 'Los abuelos de ~w son: ', [NE]),
    resp_lista(Pref, L, Vacio, R).
intencion(T, [E|_], R) :- tiene(T, [tios,tio,tia,tias]), !,
    conjunto(X, tio(X,E), L), nombre(E, NE),
    format(atom(Vacio), 'No tengo registrados tíos de ~w.', [NE]),
    format(atom(Pref), 'Los tíos de ~w son: ', [NE]),
    resp_lista(Pref, L, Vacio, R).
intencion(T, [E|_], R) :- tiene(T, [descendientes,descendencia]), !,
    conjunto(X, descendiente(X,E), L), nombre(E, NE),
    format(atom(Vacio), 'No tengo registrados descendientes de ~w.', [NE]),
    format(atom(Pref), 'Los descendientes de ~w son: ', [NE]),
    resp_lista(Pref, L, Vacio, R).
intencion(T, [E|_], R) :- tiene(T, [ancestros,antepasados]), !,
    conjunto(X, descendiente(E,X), L), nombre(E, NE),
    format(atom(Vacio), 'No tengo registrados ancestros de ~w.', [NE]),
    format(atom(Pref), 'Los ancestros de ~w son: ', [NE]),
    resp_lista(Pref, L, Vacio, R).
intencion(T, [E|_], R) :- tiene(T, [esposo,esposa,pareja,casado,casada,marido,conyuge]), !,
    conjunto(X, casados(E,X), L), nombre(E, NE),
    format(atom(Vacio), 'No tengo registrada una pareja de ~w.', [NE]),
    format(atom(Pref), 'La pareja de ~w es ', [NE]),
    resp_lista(Pref, L, Vacio, R).

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
intencion(T, [E|_], R) :- tiene(T, [mato,derroto,vencio,asesino]), categoria(E, criatura), !,
    conjunto(X, mato(X,E), L), nombre(E, NE), gen(E, O),
    format(atom(Vacio), 'No tengo registrado quién derrotó a ~w.', [NE]),
    format(atom(Pref), '~w fue derrotad~w por ', [NE,O]),
    resp_lista(Pref, L, Vacio, R).
intencion(T, [E|_], R) :- tiene(T, [mato,derroto,vencio,asesino]), !,
    conjunto(X, mato(E,X), L), nombre(E, NE),
    format(atom(Vacio), 'No tengo registradas criaturas derrotadas por ~w.', [NE]),
    format(atom(Pref), '~w derrotó a ', [NE]),
    resp_lista(Pref, L, Vacio, R).
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

% 4.10 Ficha general: "quien es X" / "que es X"
intencion(_, [E|_], R) :- !, ficha_texto(E, R).

% ---------- 5. TABLAS DE VOCABULARIO ----------
rel_palabra(padre,padre).     rel_palabra(madre,madre).
rel_palabra(hijo,hijo).       rel_palabra(hija,hijo).
rel_palabra(hermano,hermano). rel_palabra(hermana,hermano).
rel_palabra(hermanos,hermano). rel_palabra(hermanas,hermano).
rel_palabra(abuelo,abuelo).   rel_palabra(abuela,abuelo).
rel_palabra(tio,tio).         rel_palabra(tia,tio).
rel_palabra(descendiente,descendiente).
rel_palabra(esposo,casados).  rel_palabra(esposa,casados).
rel_palabra(casado,casados).  rel_palabra(casados,casados).
rel_palabra(pareja,casados).  rel_palabra(marido,casados).

% rel_texto(+Predicado, +Sujeto, -Palabra): palabra con el genero del sujeto
rel_texto(padre, _, padre) :- !.
rel_texto(madre, _, madre) :- !.
rel_texto(descendiente, _, descendiente) :- !.
rel_texto(casados, _, casados) :- !.
rel_texto(tio, A, T) :- !, ( gen(A, a) -> T = 'tía' ; T = 'tío' ).
rel_texto(Pred, A, T) :- gen(A, O), sub_atom(Pred, 0, _, 1, Raiz), atom_concat(Raiz, O, T).

cat_palabra(olimpico,olimpico). cat_palabra(olimpica,olimpico).
cat_palabra(titan,titan).       cat_palabra(titanide,titan).
cat_palabra(heroe,heroe).       cat_palabra(semidios,semidios).
cat_palabra(mortal,mortal).     cat_palabra(primordial,primordial).
cat_palabra(criatura,criatura). cat_palabra(monstruo,criatura).
cat_palabra(ctonico,ctonico).   cat_palabra(ctonica,ctonico).
cat_palabra(dios,divino).       cat_palabra(diosa,divino_f).

cat_etiqueta(Cat, _, Et) :- cat_texto(Cat, Et), !.
cat_etiqueta(_, W, W).

divinidad(C) :- memberchk(C, [olimpico,ctonico,dios_menor,titan,primordial]).
es_de_categoria(A, divino)   :- !, categoria(A, C), divinidad(C), ficha(A,_,m).
es_de_categoria(A, divino_f) :- !, categoria(A, C), divinidad(C), ficha(A,_,f).
es_de_categoria(A, Cat)      :- categoria(A, Cat).

cat_plural(olimpicos,olimpico,'Los dioses olímpicos registrados son').
cat_plural(olimpicas,olimpico,'Los dioses olímpicos registrados son').
cat_plural(titanes,titan,'Los titanes registrados son').
cat_plural(heroes,heroe,'Los héroes registrados son').
cat_plural(semidioses,semidios,'Los semidioses registrados son').
cat_plural(primordiales,primordial,'Las divinidades primordiales son').
cat_plural(monstruos,criatura,'Las criaturas registradas son').
cat_plural(criaturas,criatura,'Las criaturas registradas son').
cat_plural(ctonicos,ctonico,'Las divinidades del inframundo registradas son').
cat_plural(dioses,olimpico,'Los dioses olímpicos registrados son').

cat_texto(primordial,'divinidad primordial'). cat_texto(titan,'titán').
cat_texto(olimpico,'divinidad olímpica').     cat_texto(dios_menor,'divinidad menor').
cat_texto(ctonico,'divinidad ctónica (del inframundo)').
cat_texto(semidios,'semidiós').               cat_texto(heroe,'héroe').
cat_texto(mortal,'mortal').                   cat_texto(ninfa,'ninfa').
cat_texto(nereida,'nereida').                 cat_texto(criatura,'criatura mitológica').

% ---------- 6. FICHA GENERAL ----------
ficha_texto(E, R) :-
    nombre(E, NE),
    conjunto(C, categoria(E,C), Cs),
    findall(Tx, (member(C0,Cs), cat_texto(C0,Tx)), Ts),
    ( Ts == [] -> P1 = '' ; unir(Ts, TT), format(atom(P1), '~w es ~w. ', [NE,TT]) ),
    ( descripcion(E, Desc) -> format(atom(P0), 'Descripción: ~w. ', [Desc]) ; P0 = '' ),
    conjunto(D, dominio(E,D), Ds),
    ( Ds == [] -> P2 = '' ; lista_txt(Ds, DT), format(atom(P2), 'Dominios: ~w. ', [DT]) ),
    conjunto(S, simbolo(E,S), Ss),
    ( Ss == [] -> P3 = '' ; lista_txt(Ss, ST), format(atom(P3), 'Símbolos: ~w. ', [ST]) ),
    conjunto(P, progenitor(P,E), Ps),
    ( Ps == [] -> P4 = '' ; lista(Ps, PT), gen(E, O), format(atom(P4), 'Hij~w de ~w. ', [O,PT]) ),
    ( romano(E, N) -> format(atom(P5), 'Equivalente romano: ~w.', [N]) ; P5 = '' ),
    atomic_list_concat([P1,P0,P2,P3,P4,P5], R0),
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
        ;   recargar_kb_si_cambio,
            responder(Tr, R), format("~w~n", [R]), flush_output, bucle(P)
        )
    ).
