% cities(ID, IATA, Name, Latitude, Longitude, Vibes, AvgHotelPrice, Events)
city(1, 'BER', 'Berlin', 52.52, 13.40, [art=5, nightlife=4, eco_score=8], 80, [concert(2025,6,15)]).
city(2, 'CDG', 'Paris', 48.85, 2.35, [art=5, food=4, eco_score=6], 120, [football(2025,7,20)]).
city(3, 'AMS', 'Amsterdam', 52.37, 4.90, [art=3, nightlife=5, eco_score=9], 100, []).
city(4, 'MAD', 'Madrid', 40.42, -3.70, [food=5, history=4, eco_score=5], 90, [concert(2025,8,10)]).
city(5, 'CPH', 'Copenhagen', 55.68, 12.57, [eco_score=9, design=4], 150, []).

% users(UserID, OriginIATA, MaxBudget, Interests)
user(1, 'LHR', 800, [art, eco]).
user(2, 'JFK', 1000, [food, nightlife]).
user(3, 'SFO', 1200, [eco, design]).

% Cities with eco_score >= 7
eco_city(City) :- city(_, _, City, _, _, Vibes, _, _), member(eco_score=Score, Vibes), Score >= 7.

% Cities matching at least 2 interests from any user
interest_match(City) :-
    user(_, _, _, Interests),
    city(_, _, City, _, _, Vibes, _, _),
    count_matching_interests(Vibes, Interests, Count),
    Count >= 2.

count_matching_interests(Vibes, Interests, Count) :-
    findall(_, (member(Interest, Interests), member(Interest=_, Vibes)), Matches),
    length(Matches, Count).


% Cities with events in the next 6 months
has_upcoming_events(City) :-
    city(_, _, City, _, _, _, _, Events),
    Events \= [],
    member(Event, Events),
    event_within_months(Event, 6).

event_within_months(Event, Months) :-
    get_current_date(CurrentYear, CurrentMonth, _),
    Event =.. [_, Year, Month, _],
    (Year =:= CurrentYear, Month =< CurrentMonth + Months;
     Year =:= CurrentYear + 1, CurrentMonth + Months >= 12).

% Top destinations: eco-friendly + interest match + affordable + events
recommendation(City, Score) :-
    eco_city(City),
    interest_match(City),
    affordable(City),
    has_upcoming_events(City),
    calculate_score(City, Score).
    

% Scoring: eco (40%) + interests (30%) + budget (20%) + events (10%)
calculate_score(City, Score) :-
    city(_, _, City, _, _, Vibes, _, Events),
    (member(eco_score=EScore, Vibes) -> EcoPoints = EScore * 0.4 ; EcoPoints = 0),
    interest_score(Vibes, IntPoints),  % Sum of matched interest ratings
    budget_score(City, BudgetPoints),  % 100 - (total_cost / budget %)
    (Events \= [] -> EventPoints = 10 ; EventPoints = 0),
    Score is EcoPoints + (IntPoints * 0.3) + (BudgetPoints * 0.2) + EventPoints.