from database.enums import MatchResult, MatchType


###############################################################################
#                                 MATCH TYPE                                  #
###############################################################################


async def get_normalized_match_type(match_type: str) -> MatchType:
    normalized_match_type = None
    for match_option in MatchType:
        if str(match_option.value).casefold() == match_type.casefold():
            normalized_match_type = match_option
            break
    if not normalized_match_type:
        if match_type.casefold() in [
            "assign".casefold(),
            "assigns".casefold(),
            "assigned".casefold(),
            "official".casefold(),
        ]:
            normalized_match_type = MatchType.ASSIGNED
        if match_type.casefold() in [
            "postpone".casefold(),
            "postpones".casefold(),
            "postponed".casefold(),
        ]:
            normalized_match_type = MatchType.POSTPONED
        if match_type.casefold() in [
            "challenge".casefold(),
            "challenges".casefold(),
            "challenged".casefold(),
        ]:
            normalized_match_type = MatchType.CHALLENGE

    return normalized_match_type


###############################################################################
#                                   OUTCOME                                   #
###############################################################################


async def get_normalized_outcome(outcome: str) -> MatchResult:
    """Normalize the outcome of the match"""
    normalized_outcome: MatchResult = None
    for outcome_option in MatchResult:
        if str(outcome_option.value).casefold() == outcome.casefold():
            normalized_outcome = outcome_option
            break
    if not normalized_outcome:
        if outcome.casefold() in [
            "tie".casefold(),
            "ties".casefold(),
            "tied".casefold(),
            "draw".casefold(),
            "draws".casefold(),
            "drawn".casefold(),
            "equal".casefold(),
        ]:
            normalized_outcome = MatchResult.DRAW
        if outcome.casefold() in [
            "win".casefold(),
            "wins".casefold(),
            "won".casefold(),
            "winner".casefold(),
            "victor".casefold(),
            "victory".casefold(),
            "victorious".casefold(),
        ]:
            normalized_outcome = MatchResult.WIN
        if outcome.casefold() in [
            "lose".casefold(),
            "loses".casefold(),
            "loss".casefold(),
            "lost".casefold(),
            "loser".casefold(),
            "defeat".casefold(),
            "defeated".casefold(),
        ]:
            normalized_outcome = MatchResult.LOSS
    return normalized_outcome


async def get_reversed_outcome(outcome: MatchResult) -> MatchResult:
    """Reverse the outcome of the match"""
    transform_dict = {
        MatchResult.WIN: MatchResult.LOSS,
        MatchResult.LOSS: MatchResult.WIN,
        MatchResult.DRAW: MatchResult.DRAW,
    }
    if outcome in transform_dict.keys():
        return transform_dict[outcome]
    elif outcome:
        raise ValueError(f"Outcome '{outcome}' not available")


async def is_outcome_consistent_with_scores(
    outcome: MatchResult, scores: list[list[int | None]]
) -> bool:
    """Check if the outcome is consistent with the scores"""
    win = 0
    loss = 0
    for round_scores in scores:
        if round_scores[0] is None or round_scores[1] is None:
            continue
        if round_scores[0] > round_scores[1]:
            win += 1
        elif round_scores[0] < round_scores[1]:
            loss += 1
    if win > loss:
        return outcome == MatchResult.WIN
    if win < loss:
        return outcome == MatchResult.LOSS
    if win == loss:
        return outcome == MatchResult.DRAW
    return False


###############################################################################
#                                   SCORES                                    #
###############################################################################


async def is_score_structure_valid(scores: list[list[int | None]]) -> bool:
    """Validate the format of the scores list
    Whether or not the scores match the format: scores[round][team] = score
    """
    if len(scores) != 3:
        return False
    for round_scores in scores:
        if len(round_scores) != 2:
            return False
        for score in round_scores:
            if isinstance(score, int):
                continue
            if score is None:
                if round_scores[0] == round_scores[1]:
                    break
            return False
    return True


async def get_scores_from_list(scores: list[int | None]) -> list[list[int | None]]:
    """Convert a list of scores into a list of rounds with scores
    intput: scores[round_and_team] = score
    output: scores[round][team] = score
    Note: assumes exactly 2 teams
    """
    return [
        [scores[0], scores[1]],
        [scores[2], scores[3]],
        [scores[4], scores[5]],
    ]


async def get_reversed_scores(
    scores: list[list[int | None]] = None,
) -> list[list[int | None]]:
    """Reverse the scores of the match
    intput and output in the form of `scores[round][team] = score`
    rounds maintain order, teams are reversed
    """
    reversed_scores = [
        [scores[0][1], scores[0][0]],
        [scores[1][1], scores[1][0]],
        [scores[2][1], scores[2][0]],
    ]
    return reversed_scores


async def get_scores_display_dict(scores: list[list[int | None]]) -> dict[str, str]:
    """Convert a list of scores into a dict of rounds with scores
    intput: scores[round][team] = score
    output: scores[round] = "team_a_score : team_b_score"
    """
    # Convert each score to a 3 character string
    for i in range(3):
        for j in range(2):
            if isinstance(scores[i][j], str):
                if scores[i][j] == "":
                    scores[i][j] = None
                else:
                    scores[i][j] = int(scores[i][j])
            if isinstance(scores[i][j], int):
                if j == 0:
                    scores[i][j] = str(scores[i][j]).rjust(3)
                if j == 1:
                    scores[i][j] = str(scores[i][j]).rjust(3)
            else:
                if j == 0:
                    scores[i][j] = "   "
                if j == 1:
                    scores[i][j] = "   "
    # Populate the display_scores dict
    display_scores = {
        "round_1": f"{scores[0][0]} :{scores[0][1]} ",
        "round_2": f"{scores[1][0]} :{scores[1][1]} ",
        "round_3": f"{scores[2][0]} :{scores[2][1]} ",
    }
    return display_scores
