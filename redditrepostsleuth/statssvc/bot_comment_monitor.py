from datetime import datetime, timedelta

from redditrepostsleuth.core.config import Config
from redditrepostsleuth.core.db.databasemodels import BotComment, Comment
from redditrepostsleuth.core.db.uow.unitofworkmanager import UnitOfWorkManager
from redditrepostsleuth.core.logging import log
from redditrepostsleuth.core.services.reddit_manager import RedditManager
from redditrepostsleuth.core.util.reddithelpers import get_reddit_instance


class BotCommentMonitor:

    def __init__(self, reddit: RedditManager, uowm: UnitOfWorkManager, config: Config):
        self.reddit = reddit
        self.uowm = uowm
        if config:
            self.config = config
        else:
            self.config = Config()


    def check_comments(self):
        with self.uowm.start() as uow:
            comments = uow.bot_comment.get_after_date(datetime.utcnow() - timedelta(hours=8))
            for comment in comments:
                self._process_comment(comment)
                uow.commit()

    def _process_comment(self, bot_comment: BotComment):
        reddit_comment = self.reddit.comment(bot_comment.comment_id)

        if not reddit_comment:
            log.error('Failed to locate comment %s', bot_comment.comment_id)
            return

        bot_comment.karma = self._get_score(reddit_comment)
        print(bot_comment.karma)
        if bot_comment.karma <= -5:
            log.info('Comment %s has karma of %s.  Flagging for review', bot_comment.comment_id, bot_comment.karma)
            bot_comment.needs_review = True

    def _get_score(self, comment: Comment):
        try:
            return comment.score
        except Exception as e:
            log.error('Failed to get score for comment %s', comment.id)

