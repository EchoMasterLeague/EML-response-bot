from database.enums import MatchResult


### Outcome ###


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


### Scores ###
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
    print("scores", scores)
    for i in range(3):
        for j in range(2):
            print(i, j, scores[i][j])
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
