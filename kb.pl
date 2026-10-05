:- encoding(utf8).
% =====================================================================
% BASE DE CONOCIMIENTO: MITOLOGIA GRIEGA (logica de primer orden)
% Fuente unica: la usan el chatbot Prolog y el chatbot LLM.
% Para agregar conocimiento basta con anadir hechos (no hay que tocar
% nada mas). Ids en minuscula y sin tildes.
% =====================================================================
:- discontiguous ficha/3, categoria/2, progenitor/2, pareja/2, dominio/2,
                 simbolo/2, residencia/2, romano/2, mato/2, hazana/2.

% ---------- HECHOS ----------
% ficha(Id, 'Nombre', Genero)   Genero: m | f
ficha(caos,'Caos',f).        ficha(gaia,'Gaia',f).        ficha(urano,'Urano',m).
ficha(cronos,'Cronos',m).    ficha(rea,'Rea',f).          ficha(oceano,'Océano',m).
ficha(japeto,'Jápeto',m).    ficha(ceo,'Ceo',m).          ficha(febe,'Febe',f).
ficha(atlas,'Atlas',m).      ficha(prometeo,'Prometeo',m). ficha(epimeteo,'Epimeteo',m).
ficha(leto,'Leto',f).        ficha(metis,'Metis',f).      ficha(maya,'Maya',f).
ficha(zeus,'Zeus',m).        ficha(hera,'Hera',f).        ficha(poseidon,'Poseidón',m).
ficha(hades,'Hades',m).      ficha(demeter,'Deméter',f).  ficha(hestia,'Hestia',f).
ficha(atenea,'Atenea',f).    ficha(apolo,'Apolo',m).      ficha(artemisa,'Artemisa',f).
ficha(ares,'Ares',m).        ficha(afrodita,'Afrodita',f). ficha(hefesto,'Hefesto',m).
ficha(hermes,'Hermes',m).    ficha(dionisio,'Dionisio',m). ficha(hebe,'Hebe',f).
ficha(persefone,'Perséfone',f). ficha(anfitrite,'Anfítrite',f). ficha(triton,'Tritón',m).
ficha(semele,'Sémele',f).    ficha(alcmena,'Alcmena',f).  ficha(danae,'Dánae',f).
ficha(heracles,'Heracles',m). ficha(perseo,'Perseo',m).   ficha(teseo,'Teseo',m).
ficha(aquiles,'Aquiles',m).  ficha(peleo,'Peleo',m).      ficha(tetis,'Tetis',f).
ficha(medusa,'Medusa',f).    ficha(hidra,'la Hidra de Lerna',f).
ficha(minotauro,'el Minotauro',m). ficha(piton,'Pitón',m).

% categoria(Id, Cat)  Cat: primordial | titan | olimpico | semidios | heroe | mortal | ninfa | criatura | nereida | dios_menor
categoria(caos,primordial). categoria(gaia,primordial). categoria(urano,primordial).
categoria(cronos,titan). categoria(rea,titan). categoria(oceano,titan). categoria(japeto,titan).
categoria(ceo,titan). categoria(febe,titan). categoria(atlas,titan). categoria(prometeo,titan).
categoria(epimeteo,titan). categoria(leto,titan). categoria(metis,titan).
categoria(maya,ninfa).
categoria(zeus,olimpico). categoria(hera,olimpico). categoria(poseidon,olimpico).
categoria(demeter,olimpico). categoria(hestia,olimpico). categoria(atenea,olimpico).
categoria(apolo,olimpico). categoria(artemisa,olimpico). categoria(ares,olimpico).
categoria(afrodita,olimpico). categoria(hefesto,olimpico). categoria(hermes,olimpico).
categoria(dionisio,olimpico).
categoria(hades,dios_menor). categoria(persefone,dios_menor). categoria(hebe,dios_menor).
categoria(anfitrite,nereida). categoria(tetis,nereida). categoria(triton,dios_menor).
categoria(heracles,semidios). categoria(perseo,semidios). categoria(aquiles,semidios).
categoria(heracles,heroe). categoria(perseo,heroe). categoria(aquiles,heroe). categoria(teseo,heroe).
categoria(semele,mortal). categoria(alcmena,mortal). categoria(danae,mortal). categoria(peleo,mortal).
categoria(medusa,criatura). categoria(hidra,criatura). categoria(minotauro,criatura). categoria(piton,criatura).

% progenitor(Padre_o_Madre, Hijo)   (version de Hesiodo)
progenitor(gaia,cronos).  progenitor(urano,cronos).
progenitor(gaia,rea).     progenitor(urano,rea).
progenitor(gaia,oceano).  progenitor(urano,oceano).
progenitor(gaia,japeto).  progenitor(urano,japeto).
progenitor(gaia,ceo).     progenitor(urano,ceo).
progenitor(gaia,febe).    progenitor(urano,febe).
progenitor(japeto,atlas). progenitor(japeto,prometeo). progenitor(japeto,epimeteo).
progenitor(ceo,leto).     progenitor(febe,leto).
progenitor(cronos,zeus).  progenitor(rea,zeus).
progenitor(cronos,hera).  progenitor(rea,hera).
progenitor(cronos,poseidon). progenitor(rea,poseidon).
progenitor(cronos,hades). progenitor(rea,hades).
progenitor(cronos,demeter). progenitor(rea,demeter).
progenitor(cronos,hestia). progenitor(rea,hestia).
progenitor(zeus,ares).    progenitor(hera,ares).
progenitor(zeus,hefesto). progenitor(hera,hefesto).
progenitor(zeus,hebe).    progenitor(hera,hebe).
progenitor(zeus,apolo).   progenitor(leto,apolo).
progenitor(zeus,artemisa). progenitor(leto,artemisa).
progenitor(zeus,hermes).  progenitor(maya,hermes).
progenitor(zeus,atenea).  progenitor(metis,atenea).
progenitor(zeus,dionisio). progenitor(semele,dionisio).
progenitor(zeus,persefone). progenitor(demeter,persefone).
progenitor(zeus,heracles). progenitor(alcmena,heracles).
progenitor(zeus,perseo).  progenitor(danae,perseo).
progenitor(urano,afrodita).
progenitor(poseidon,triton). progenitor(anfitrite,triton).
progenitor(peleo,aquiles). progenitor(tetis,aquiles).

% pareja(A,B)  (matrimonio o union reconocida)
pareja(zeus,hera).       pareja(cronos,rea).    pareja(hades,persefone).
pareja(poseidon,anfitrite). pareja(hefesto,afrodita). pareja(peleo,tetis).

% dominio(Id, Palabra)  (una palabra por hecho)
dominio(zeus,cielo). dominio(zeus,trueno). dominio(zeus,rayo).
dominio(poseidon,mar). dominio(poseidon,terremotos). dominio(poseidon,caballos).
dominio(hades,inframundo). dominio(hades,muerte). dominio(hades,riquezas).
dominio(hera,matrimonio). dominio(hera,familia).
dominio(demeter,agricultura). dominio(demeter,cosecha).
dominio(hestia,hogar). dominio(hestia,fuego_sagrado).
dominio(atenea,sabiduría). dominio(atenea,estrategia). dominio(atenea,artesanía).
dominio(apolo,sol). dominio(apolo,música). dominio(apolo,profecía). dominio(apolo,medicina).
dominio(artemisa,caza). dominio(artemisa,luna). dominio(artemisa,bosques).
dominio(ares,guerra).
dominio(afrodita,amor). dominio(afrodita,belleza).
dominio(hefesto,fragua). dominio(hefesto,fuego). dominio(hefesto,metalurgia).
dominio(hermes,comercio). dominio(hermes,viajeros). dominio(hermes,mensajes).
dominio(dionisio,vino). dominio(dionisio,teatro). dominio(dionisio,fiesta).
dominio(hebe,juventud). dominio(persefone,primavera).

% simbolo(Id, Simbolo)
simbolo(zeus,rayo). simbolo(zeus,águila). simbolo(zeus,roble).
simbolo(hera,pavo_real). simbolo(hera,granada).
simbolo(poseidon,tridente). simbolo(poseidon,caballo). simbolo(poseidon,delfín).
simbolo(hades,casco_de_invisibilidad). simbolo(hades,cerbero).
simbolo(demeter,espiga). simbolo(demeter,antorcha).
simbolo(hestia,hogar). simbolo(atenea,lechuza). simbolo(atenea,olivo). simbolo(atenea,escudo_égida).
simbolo(apolo,lira). simbolo(apolo,laurel). simbolo(apolo,arco).
simbolo(artemisa,arco). simbolo(artemisa,luna_creciente). simbolo(artemisa,ciervo).
simbolo(ares,lanza). simbolo(ares,buitre). simbolo(afrodita,paloma). simbolo(afrodita,rosa).
simbolo(hefesto,martillo). simbolo(hefesto,yunque).
simbolo(hermes,caduceo). simbolo(hermes,sandalias_aladas).
simbolo(dionisio,tirso). simbolo(dionisio,uva). simbolo(heracles,maza). simbolo(heracles,piel_de_león).
simbolo(perseo,escudo_de_bronce). simbolo(aquiles,talón).

% residencia(Id, Lugar)
residencia(zeus,'el monte Olimpo').    residencia(hera,'el monte Olimpo').
residencia(atenea,'el monte Olimpo').  residencia(apolo,'el monte Olimpo').
residencia(artemisa,'el monte Olimpo'). residencia(ares,'el monte Olimpo').
residencia(afrodita,'el monte Olimpo'). residencia(hefesto,'el monte Olimpo').
residencia(hermes,'el monte Olimpo').  residencia(hestia,'el monte Olimpo').
residencia(dionisio,'el monte Olimpo'). residencia(demeter,'el monte Olimpo').
residencia(poseidon,'un palacio en el fondo del mar'). residencia(hades,'el inframundo').
residencia(persefone,'el inframundo').  residencia(cronos,'el Tártaro').

% romano(IdGriego, 'Nombre romano')
romano(zeus,'Júpiter'). romano(hera,'Juno'). romano(poseidon,'Neptuno').
romano(hades,'Plutón'). romano(demeter,'Ceres'). romano(hestia,'Vesta').
romano(atenea,'Minerva'). romano(apolo,'Apolo'). romano(artemisa,'Diana').
romano(ares,'Marte'). romano(afrodita,'Venus'). romano(hefesto,'Vulcano').
romano(hermes,'Mercurio'). romano(dionisio,'Baco'). romano(cronos,'Saturno').
romano(heracles,'Hércules'). romano(persefone,'Prosérpina'). romano(hebe,'Juventas').

% mato(Heroe, Criatura)  /  hazana(Heroe, 'Descripcion')
mato(perseo,medusa). mato(heracles,hidra). mato(teseo,minotauro). mato(apolo,piton).
hazana(perseo,'decapitó a Medusa con ayuda de un escudo pulido').
hazana(perseo,'rescató a Andrómeda de un monstruo marino').
hazana(heracles,'realizó los doce trabajos para el rey Euristeo').
hazana(heracles,'derrotó a la Hidra de Lerna').
hazana(teseo,'mató al Minotauro en el laberinto de Creta').
hazana(aquiles,'fue el mayor guerrero griego en la guerra de Troya').
hazana(prometeo,'robó el fuego de los dioses para entregárselo a los humanos').

% ---------- REGLAS ----------
padre(P,H)   :- progenitor(P,H), ficha(P,_,m).
madre(M,H)   :- progenitor(M,H), ficha(M,_,f).
hijo(H,P)    :- progenitor(P,H).
hermano(X,Y) :- progenitor(P,X), progenitor(P,Y), X \= Y.      % comparte al menos un progenitor
abuelo(A,N)  :- progenitor(A,P), progenitor(P,N).
tio(T,S)     :- progenitor(P,S), hermano(T,P).
casados(X,Y) :- pareja(X,Y) ; pareja(Y,X).
descendiente(D,A) :- progenitor(A,D).
descendiente(D,A) :- progenitor(P,D), descendiente(P,A).
