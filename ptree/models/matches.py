from django.db import models
import abc

class MatchManager(models.Manager):
    def next_open_match(self, request):
        """Get the next match that is accepting participants.
        May raise a StopIteration exception if there are no open matches.
        """
        from ptree.models.common import Symbols
        matches = super(MatchManager, self).get_query_set().all()
        return (m for m in matches if m.treatment.code == request.session[Symbols.treatment_code] and m.is_ready_for_next_participant()).next()

class BaseMatch(models.Model):
    """
    Base class for all Matches.
    
    A Match is a particular instance of a game being played,
    and holds the results of that instance, i.e. what the score was, who got paid what.

    "Match" is used in the sense of "boxing match".
    
    Example of a Match: "dictator game between users Alice & Bob, where Alice gave $0.50"

    If a piece of data is specific to a particular participant, you should store it in a Participant object instead.
    For example, in the Prisoner's Dilemma, each Participant has to decide between "Cooperate" and "Compete".
    You should store these on the Participant object as participant.decision,
    NOT "match.participant_1_decision" and "match.participant_2_decision".

    The exception is if the game is asymmetric, and participant_1_decision and participant_2_decision have different data types.
    """

    #: when the game was started
    time_started = models.DateTimeField(auto_now_add = True)

    objects = MatchManager()

    #@abc.abstractmethod
    def is_ready_for_next_participant(self):
        """
        Needs to be implemented by child classes.
        Whether the game is ready for another participant to be added.
        """
        raise NotImplementedError()

    def is_full(self):
        """
        Whether the match is full (i.e. no more ``Participant``s can be assigned).
        """
        return len(self.participants()) >= self.treatment.participants_per_match

    def is_finished(self):
        """Whether the match is completed."""
        return self.is_full() and [participant.is_finished for participant in self.participants()]

    def participants(self):
        """
        Returns the ``Participant`` objects in this match.
        Syntactic sugar ``for self.participant_set.all()``
        """
        return self.participant_set.all()

    
    class Meta:
        abstract = True
        verbose_name_plural = "matches"

class MatchInTwoPersonAsymmetricGame(BaseMatch):
    participant_1 = models.ForeignKey('Participant', related_name = "games_as_participant_1")
    participant_2 = models.ForeignKey('Participant', related_name = "games_as_participant_2", null = True)

    class Meta:
        abstract = True

    def is_ready_for_next_participant(self):
        return self.participant_1 and self.participant_1.is_finished_playing() and not self.participant_2

class MatchOffer(BaseMatch):
    amount_offered = models.PositiveIntegerField(null = True) # amount the first player offers to second player

