:- use_module(library(http/json)).
:- use_module(library(lists)).
:- use_module(library(apply)).
:- use_module(library(filesex)). % Needed for make_directory/1, exists_directory/1

% --- Keep ALL your other existing predicates ---
% ensure_data_directory/0, num_users/1, overall_city_desti/2, city_dist/3,
% overall_city_dist/2, count_occurrences/3, overall_city_vibe/2, filter_vibe/3,
% score_and_rank_cities/2, score_city/2, fit_to_score/2, display_results/1,
% display_results/2, take_first/3, export_ranked_cities_to_json/2,
% main/0, main/1, main/2
% --- ... (Assume they are all here) ... ---

% --- MODIFIED Predicate ---

ranked_cities_to_dicts(RankedCities, DictList) :-
    ranked_cities_to_dicts(RankedCities, 1, DictList).

ranked_cities_to_dicts([], _, []).
ranked_cities_to_dicts([Score-City | RestRanked], Rank, [CityDict | RestDicts]) :-
    % Retrieve the fits (as before)
    (overall_city_desti(City, DestiFit) -> true ; DestiFit = 'NoneDest'),
    (overall_city_dist(City, DistFit)   -> true ; DistFit = 'LongDist'),
    (overall_city_vibe(City, VibeFit)   -> true ; VibeFit = 'None'),

    % Lookup IATA code (as before)
    ( city_iata(City, Iata) -> true ; Iata = 'unknown' ),

    % --- NEW: Lookup Latitude and Longitude ---
    % Use 0.0 as default if lat/long are not found for the city
    ( city_lat(City, Lat)   -> true ; Lat = 0.0 ),
    ( city_long(City, Long) -> true ; Long = 0.0 ),

    % Create the dictionary for this city, now including IATA, Lat, and Long
    CityDict = json{
        rank: Rank,
        score: Score,
        city: City,               % City name (e.g., 'London')
        iata: Iata,               % IATA code (e.g., 'LHR' or 'unknown')
        lat: Lat,                 % Latitude (e.g., 51.5 or 0.0)
        long: Long,               % Longitude (e.g., -0.1 or 0.0)
        destination_fit: DestiFit,
        distance_fit: DistFit,
        vibe_fit: VibeFit
    },

    NextRank is Rank + 1,
    ranked_cities_to_dicts(RestRanked, NextRank, RestDicts).


% --- Keep the rest of your code unchanged ---

ensure_data_directory :-
    (exists_directory('../data') -> true ; make_directory('../data')).

num_users(Num) :-
    findall(User, user_city(User, _), UserList),
    length(UserList, Num).

overall_city_desti(City, Fit) :-
    % Corrected logic: Count users interested in THIS city, not all cities
    findall(User, user_city(User, City), InterestedUsers), % Find users whose city IS City
    length(InterestedUsers, NInterest),
    num_users(NumUsers),
    ( NumUsers == 0 -> Avg = 0 ; Avg is NInterest / NumUsers ), % Avoid division by zero
    (
        Avg > 0.50 -> Fit = 'HighDest' ;
        Avg =< 0.50 , Avg > 0.25 -> Fit = 'MidDest' ;
        Avg =< 0.25 , Avg > 0.001 -> Fit = 'LowDest' ; % Adjusted boundary
        Avg =< 0.001 -> Fit = 'NoneDest'
    ).

city_dist(City, User, Dist) :-
    user_city(User, UCit),
    city_long(City, DestLong),
    city_lat(City, DestLat),
    city_long(UCit, OrigLong),
    city_lat(UCit, OrigLat),

    % Check if coordinates are valid numbers before calculation
    ( number(DestLat), number(DestLong), number(OrigLat), number(OrigLong) ->
        P is 0.017453292519943295,
        A is (0.5 - cos((DestLat - OrigLat) * P) / 2 + cos(OrigLat * P) * cos(DestLat * P) * (1 - cos((DestLong - OrigLong) * P)) / 2),
        % Handle potential domain error for asin if A is slightly > 1 or < 0 due to precision
        ( A > 1.0 -> ASinArg = 1.0 ; A < 0.0 -> ASinArg = 0.0 ; ASinArg = A ),
        Dist is (12742 * asin(sqrt(ASinArg)))
    ;   % If any coordinate is not a number, distance is undefined (or set a default max?)
        Dist = 99999 % Or maybe fail? Assigning a large distance might be better for ranking
    ).


pairs_values([_-V|Pairs], [V|Values]) :- pairs_values(Pairs, Values).
pairs_values([], []).

overall_city_dist(City, Fit) :-
    findall(Dist, city_dist(City, _, Dist), CitiesDists),
    % Filter out potential large default distances if coordinates were missing
    include(\=(99999), CitiesDists, ValidDists),
    ( ValidDists == [] ->
        % If no valid distances, maybe default to LongDist or based on other factors?
        Avg = 99999 % Indicate no valid average distance
    ;
        sum_list(ValidDists, Sum),
        length(ValidDists, Count),
        Avg is Sum / Count
    ),
    (
        Avg > 5000 -> Fit = 'LongDist' ;
        Avg =< 5000 , Avg > 1000 -> Fit = 'MediumDist' ;
        Avg =< 1000 , Avg > 150 -> Fit = 'ShortDist' ;
        Avg =< 150 -> Fit = 'Local' % This includes the case Avg=99999 if ValidDists was empty
                                    % which might not be desired. Consider explicit handling.
        % Maybe add specific handling for Avg = 99999 ?
        % ; Avg == 99999 -> Fit = 'UnknownDist'
    ).


count_occurrences([], _, 0).
count_occurrences([Element | Tail], Element, Count) :-
    !, % Green cut: If match, dont try the next clause
    count_occurrences(Tail, Element, TailCount),
    Count is TailCount + 1.
count_occurrences([_ | Tail], Element, Count) :-
    % Head \= Element implied by the cut in the previous clause
    count_occurrences(Tail, Element, Count).


overall_city_vibe(City, Fit) :-
    findall(Val, filter_vibe(City, _, Val), VibesList),
    ( VibesList == [] -> % Check if list is empty BEFORE sum/length
        Fit = 'None'
    ;
        sum_list(VibesList, Sum),
        length(VibesList, NumVibes), % NumVibes will be > 0 here
        Avg is Sum / NumVibes,
        (
            Avg > 3 -> Fit = 'High';
            Avg >= 2 -> Fit = 'Mid'; % Simplified condition
            Avg >= 0.1 -> Fit = 'Low' ; % Simplified condition (changed > to >=)
            Fit = 'None' % Handles Avg < 0.1
        )
    ).


filter_vibe(City, User, Length) :-
    user_preference(User, Pref),
    has_vibes(City, CList), % Assumes has_vibes/2 facts exist
    intersection(Pref, CList, Inter),
    length(Inter, Length).

score_and_rank_cities(Cities, Ranked) :-
    findall(Score-C, (member(C, Cities), score_city(C, Score-C)), ScoredCities), % More robust way
    % maplist(score_city, Cities, ScoredCities), % maplist might fail if score_city fails for any city
    keysort(ScoredCities, Sorted),
    reverse(Sorted, Ranked).

score_city(City, Score-City) :-
    % Ensure the predicates succeed, otherwise scoring fails for this city.
    % The default values inside the overall_ predicates handle missing data better.
    overall_city_desti(City, DestiFit),
    overall_city_dist(City, DistFit),
    overall_city_vibe(City, VibeFit),
    !, % If we calculated fits, commit to scoring this city
    fit_to_score(DestiFit, DestiScore),
    fit_to_score(DistFit, DistScore),
    fit_to_score(VibeFit, VibeScore),
    Score is DestiScore * 0.4 + DistScore * 0.3 + VibeScore * 0.3.

% Handle case where a city might fail scoring (e.g., missing essential data?)
% This clause might not be needed if overall_ predicates always succeed with defaults.
% score_city(City, 0.0-City) :-
%    writef('Warning: Could not calculate score for city: %w. Assigning 0.0\n', [City]).


fit_to_score('HighDest', 4.0).
fit_to_score('MidDest', 3.0).
fit_to_score('LowDest', 2.0).
fit_to_score('NoneDest', 0.1).

fit_to_score('Local', 4.0).
fit_to_score('ShortDist', 3.5).
fit_to_score('MediumDist', 2.5).
fit_to_score('LongDist', 1.0).
% fit_to_score('UnknownDist', 0.1). % Optional score for unknown distance

fit_to_score('High', 4.0).
fit_to_score('Mid', 3.0).
fit_to_score('Low', 2.0).
fit_to_score('None', 0.1).


display_results(RankedCities) :-
    format('~w~t~8+~w~t~8+~w~t~8+~w~t~8+~w~t~8+~w~n', ['Rank', 'Score', 'Dest', 'Dist', 'Vibe', 'City']),
    display_results(RankedCities, 1).

display_results([], _).
display_results([Score-City|Rest], Rank) :-
    % Use defaults if predicates fail during display (should be rare if scoring worked)
    (overall_city_desti(City, Desti) -> true ; Desti = 'N/A'),
    (overall_city_dist(City, Dist)   -> true ; Dist = 'N/A'),
    (overall_city_vibe(City, Vibe)   -> true ; Vibe = 'N/A'),
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

export_ranked_cities_to_json(DictList, Filename) :-
    ensure_data_directory, % Check/create ../data
    % Construct the path relative to the current directory using '..'
    atomic_list_concat(['../data/', Filename], OutputPath), % Use '../data/' directly
    setup_call_cleanup(
        % Open the file at the desired relative path
        open(OutputPath, write, Stream, [encoding(utf8)]),
        json_write_dict(Stream, DictList, [width(0)]),
        close(Stream)
    ).

main(Filename, NumResults) :-
    % --- Initialization ---
    write('City Recommendation System'), nl,
    write('========================='), nl, nl,
    ensure_data_directory, % Ensure ../data dir exists before trying to write or consult
    % Consult data files RELATIVE to the script location
    % These paths assume the script is in 'src' and data is in '../data'
    ( exists_file('../data/cities.pl') -> consult('../data/cities.pl')
      ; writef('ERROR: Cannot find ../data/cities.pl~n'), halt(1) ),
    ( exists_file('../data/users.pl') -> consult('../data/users.pl')
      ; writef('ERROR: Cannot find ../data/users.pl~n'), halt(1) ),
    nl,

    % --- Data Gathering & Processing ---
    write('Finding all known cities with coordinates...'), nl,
    findall(City, city_lat(City, _), AllCitiesWithLat),
    list_to_set(AllCitiesWithLat, ValidCities),
    length(ValidCities, NumCities),
    ( NumCities > 0 -> writef('%t unique cities with latitude found.~n', [NumCities])
      ; writef('WARNING: No cities with latitude found in ../data/cities.pl.~n') ),
    nl,

    write('Scoring and ranking valid cities...'), nl,
    score_and_rank_cities(ValidCities, FullRankedCities),
    length(FullRankedCities, NumRanked),
    writef('%t cities successfully ranked.~n', [NumRanked]), nl,

    % --- Selecting & Outputting Results ---
    writef('Selecting top %t results...~n', [NumResults]),
    take_first(NumResults, FullRankedCities, TopRankedCities),

    length(TopRankedCities, ActualNum),
    ( ActualNum == 0 ->
        nl, write('*** No cities found or ranked to display or export. ***'), nl,
        ( NumCities == 0 -> write('*** Check ../data/cities.pl for city_lat/2 facts. ***'), nl
          ; write('*** Check scoring logic or data consistency (e.g., user_city references). ***'), nl )
    ;
        % --- Optional: Display top N results to console ---
        nl, writef('--- Top %t Cities (Console Output) ---~n', [ActualNum]),
        display_results(TopRankedCities),
        nl,

        % --- Convert SELECTED Top N to Dictionaries and Export to JSON ---
        writef('Converting top %t results to JSON format...~n', [ActualNum]),
        ranked_cities_to_dicts(TopRankedCities, JsonDictList), % Includes IATA, Lat, Long

        % Corrected feedback message
        writef('Exporting top %t results to ../data/%w...~n', [ActualNum, Filename]),
        export_ranked_cities_to_json(JsonDictList, Filename), % Export the limited list

        nl, write('Processing complete. JSON saved.'), nl
    ).


main :-
    NumTop = 100, % Define the default number of results here
    atomic_list_concat(['ranked_cities_top', NumTop, '.json'], DefaultFilename),
    main(DefaultFilename, NumTop).


main(NumResults) :-
    ( integer(NumResults), NumResults >= 0 -> % Basic validation
        atomic_list_concat(['ranked_cities_top', NumResults, '.json'], Filename),
        main(Filename, NumResults)
    ; writef('Error: Argument must be a non-negative integer. Got: %w~n', [NumResults]),
      halt(1) % Exit with error status
    ).

% --- Initialization goal for standalone executable ---
% This runs consults automaticaQlly when the executable starts
% :- initialization(main, main). % Use this if you want main/0 to run automatically
% :- initialization(ensure_data_directory). % Ensure dir exists on startup
% :- consult('../data/cities.pl'). % Consult data files on startup
% :- consult('../data/users.pl').

% Note: If using the Makefile `-c file1 file2...` option, explicit consults here
% might be redundant or cause files to be loaded twice. Test which approach works best.