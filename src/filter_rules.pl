:- use_module(library(http/json)). % <-- ADD THIS LINE AT THE TOP
:- use_module(library(lists)). % For sum_list, length, append, reverse, keysort
:- use_module(library(apply)). % For maplist

ensure_data_directory :-
    (exists_directory('data') -> true ; make_directory('data')).

num_users(Num) :-
    findall(User, user_city(User, _), UserList),
    length(UserList, Num).

overall_city_desti(City, Fit) :-
    setof(City, Lat^Long^(city_lat(City, Lat), city_long(City, Long)), EvalList),
    length(EvalList, NInterest),
    num_users(NumUsers),
    Avg is NInterest/NumUsers,
    (Avg > 0.50 -> Fit = 'HighDest' ;
    Avg =< 0.50 , Avg > 0.25 -> Fit = 'MidDest' ; 
    Avg > 0.001 , Avg < 0.25 -> Fit = 'LowDest' ;
    Avg =< 0.001 -> Fit = 'NoneDest').


city_dist(City, User, Dist) :-
    user_city(User, UCit),
    city_long(City, DestLong), 
    city_lat(City, DestLat),
    city_long(UCit, OrigLong), 
    city_lat(UCit, OrigLat),

    P is 0.017453292519943295,
    A is (0.5 - cos((DestLat - OrigLat) * P) / 2 + cos(OrigLat * P) * cos(DestLat * P) * (1 - cos((DestLong - OrigLong) * P)) / 2),
    Dist is (12742 * asin(sqrt(A))).

%take_first(N, List, FirstN) :- length(FirstN, N), append(FirstN, _, List).
pairs_values([_-V|Pairs], [V|Values]) :- pairs_values(Pairs, Values).
pairs_values([], []).

overall_city_dist(City, Fit) :-
    findall(Dist, city_dist(City, _, Dist), Cities),
    sum_list(Cities, Sum),
    length(Cities, Count),
    (Count > 0 -> Avg is Sum / Count;
    Avg is 0),
    (Avg > 5000 -> Fit = 'LongDist' ;
    Avg =< 5000 , Avg > 1000 -> Fit = 'MediumDist' ; 
    Avg =< 1000 , Avg > 150 -> Fit = 'ShortDist' ;
    Avg =< 150 -> Fit = 'Local').

% Base case: If the list is empty, the count is 0.
count_occurrences([], _, 0).

% Recursive case 1: If the head of the list matches the Element,
% count the occurrences in the tail and add 1.
count_occurrences([Element | Tail], Element, Count) :-
    count_occurrences(Tail, Element, TailCount),
    Count is TailCount + 1.

% Recursive case 2: If the head of the list does not match the Element,
% the count is the same as the count in the tail.
count_occurrences([Head | Tail], Element, Count) :-
    Head \= Element, % Make sure the head is different from the Element
    count_occurrences(Tail, Element, Count).

overall_city_vibe(City, Fit) :-
    findall(Val, filter_vibe(City, _, Val), VibesList),
    sum_list(VibesList, Sum),
    length(VibesList, NumVibes),
    (NumVibes =:= 0 -> Fit = 'None' ;
    Avg is Sum / NumVibes,
    (Avg > 3 -> Fit = 'High';
    Avg >= 2, Avg =< 3 -> Fit = 'Mid';
    Avg < 2, Avg > 0.1-> Fit = 'Low' ;
    Avg =< 0.1 -> Fit = 'None')).

filter_vibe(City, User, Length) :- 
    user_preference(User, Pref), 
    has_vibes(City, CList), 
    intersection(Pref, CList, Inter), 
    length(Inter, Length).

score_and_rank_cities(Cities, Ranked) :-
    maplist(score_city, Cities, ScoredCities),
    keysort(ScoredCities, Sorted), % Sorts by score (ascending)
    reverse(Sorted, Ranked).      % Reverses to get highest score first

score_city(City, Score-City) :-
    (overall_city_desti(City, DestiFit) -> true ; DestiFit = 'NoneDest'), % Use default if predicate fails
    (overall_city_dist(City, DistFit) -> true ; DistFit = 'LongDist'),   % Use default if predicate fails
    (overall_city_vibe(City, VibeFit) -> true ; VibeFit = 'None'),       % Use default if predicate fails
    fit_to_score(DestiFit, DestiScore),
    fit_to_score(DistFit, DistScore),
    fit_to_score(VibeFit, VibeScore),
    Score is DestiScore * 0.4 + DistScore * 0.3 + VibeScore * 0.3.

fit_to_score('HighDest', 4.0).
fit_to_score('MidDest', 3.0).
fit_to_score('LowDest', 2.0).
fit_to_score('NoneDest', 0.1).
fit_to_score('Local', 4.0).
fit_to_score('ShortDist', 3.5).
fit_to_score('MediumDist', 2.5).
fit_to_score('LongDist', 1.0).
fit_to_score('High', 4.0).
fit_to_score('Mid', 3.0).
fit_to_score('Low', 2.0).
fit_to_score('None', 0.1).

display_results(RankedCities) :-
    format('~w~t~8+~w~t~8+~w~t~8+~w~t~8+~w~t~8+~w~n', ['Rank', 'Score', 'Dest', 'Dist', 'Vibe', 'City']),
    display_results(RankedCities, 1).

display_results([], _).
display_results([Score-City|Rest], Rank) :-
    (overall_city_desti(City, Desti) -> true ; Desti = 'NoneDest'),
    (overall_city_dist(City, Dist) -> true ; Dist = 'LongDist'),
    (overall_city_vibe(City, Vibe) -> true ; Vibe = 'None'),
    format('~d~t~8+~2f~t~8+~w~t~8+~w~t~8+~w~t~8+~w~n',
           [Rank, Score, Desti, Dist, Vibe, City]),
    NextRank is Rank + 1,
    display_results(Rest, NextRank).

take_first(0, _, []) :- !.
take_first(_, [], []) :- !.
take_first(N, [H|T], [H|R]) :-
    N > 0,
    N1 is N - 1,
    take_first(N1, T, R).

ranked_cities_to_dicts(RankedCities, DictList) :-
    ranked_cities_to_dicts(RankedCities, 1, DictList).

ranked_cities_to_dicts([], _, []).
ranked_cities_to_dicts([Score-City | RestRanked], Rank, [CityDict | RestDicts]) :-
    % Retrieve the fits (as before)
    (overall_city_desti(City, DestiFit) -> true ; DestiFit = 'NoneDest'),
    (overall_city_dist(City, DistFit) -> true ; DistFit = 'LongDist'),
    (overall_city_vibe(City, VibeFit) -> true ; VibeFit = 'None'),

    % --- NEW: Lookup IATA code ---
    % Use a default value if the IATA code is not found for the city
    ( city_iata(City, Iata) -> true ; Iata = 'unknown' ), % Assign 'unknown' if city_iata fails

    % Create the dictionary for this city, now including IATA
    CityDict = json{
        rank: Rank,
        score: Score,
        city: City,           % City name (e.g., 'London')
        'IATA': Iata,           % IATA code (e.g., 'LHR' or 'unknown')
        destination_fit: DestiFit,
        distance_fit: DistFit,
        vibe_fit: VibeFit
    },

    NextRank is Rank + 1,
    ranked_cities_to_dicts(RestRanked, NextRank, RestDicts).

export_ranked_cities_to_json(DictList, Filename) :-
    ensure_data_directory,
    atomic_list_concat(['data/', Filename], OutputPath),
    setup_call_cleanup(
        open(OutputPath, write, Stream, [encoding(utf8)]),
        json_write_dict(Stream, DictList, [width(0)]),
        close(Stream)
    ).
% --- End of existing predicates ---

main(Filename, NumResults) :-
    write('City Recommendation System'), nl,
    write('========================='), nl, nl,
    findall(City, city_lat(City, _), AllCitiesWithLat),
    list_to_set(AllCitiesWithLat, ValidCities),
    write('Scoring and ranking all valid cities...'), nl,
    score_and_rank_cities(ValidCities, FullRankedCities),
    writef('Selecting top %t results...~n', [NumResults]),
    take_first(NumResults, FullRankedCities, TopRankedCities),
    length(TopRankedCities, ActualNum),
    ( ActualNum == 0 ->
        write('No cities found or ranked to display or export.'), nl
    ;
        nl, writef('--- Top %t Cities (Console) ---~n', [ActualNum]),
        display_results(TopRankedCities),
        nl,
        writef('Converting top %t results to JSON format...~n', [ActualNum]),
        ranked_cities_to_dicts(TopRankedCities, JsonDictList),
        writef('Exporting top %t results to data/%w...~n', [ActualNum, Filename]),
        export_ranked_cities_to_json(JsonDictList, Filename),
        nl, write('Processing complete.'), nl
    ).

% Keep the other main predicates the same
main :-
    NumTop = 100,
    atomic_list_concat(['ranked_cities_top', NumTop, '.json'], DefaultFilename),
    main(DefaultFilename, NumTop).

main(NumResults) :-
    integer(NumResults), NumResults >= 0,
    atomic_list_concat(['ranked_cities_top', NumResults, '.json'], Filename),
    main(Filename, NumResults).