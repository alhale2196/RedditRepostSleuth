import json
import re
import time
from json import JSONDecodeError
from typing import Text, Dict, NoReturn

from praw import Reddit
from praw.models import Message

from redditrepostsleuth.core.config import Config
from redditrepostsleuth.core.db.databasemodels import UserReport, RepostWatch
from redditrepostsleuth.core.db.db_utils import get_db_engine
from redditrepostsleuth.core.db.uow.sqlalchemyunitofworkmanager import SqlAlchemyUnitOfWorkManager
from redditrepostsleuth.core.db.uow.unitofworkmanager import UnitOfWorkManager
from redditrepostsleuth.core.logging import log
from redditrepostsleuth.core.notification.notification_service import NotificationService
from redditrepostsleuth.core.services.eventlogging import EventLogging
from redditrepostsleuth.core.util.reddithelpers import get_reddit_instance
from redditrepostsleuth.core.util.replytemplates import TOP_POST_WATCH_SUBJECT, WATCH_ENABLED


class InboxMonitor:

    def __init__(
            self,
            uowm: UnitOfWorkManager,
            reddit: Reddit,
            event_logger: EventLogging = None,
            notification_svc: NotificationService = None
    ):
        self.notification_svc = notification_svc
        self.uowm = uowm
        self.event_logger = event_logger
        self.reddit = reddit
        self.failed_checks = []

    def check_inbox(self):
        print('[Scheduled Job] Checking Inbox Start')
        for msg in self.reddit.inbox.messages(limit=500):
            if msg.author != 'RepostSleuthBot' and msg.subject.lower() in ['false negative', 'false positive']:
                self._process_user_report(msg)
            elif TOP_POST_WATCH_SUBJECT.lower() in msg.subject.lower():
                self._process_watch_request(msg)


    def _process_watch_request(self, msg: Message) -> NoReturn:
        """
        Process someone that wants to active a watch from top posts
        :param msg: message
        """
        if not msg.replies:
            return
        if 'yes' in msg.replies[0].body.lower():
            post_id_search = re.search(r'(?:https://redd.it/)([A-Za-z0-9]{6})', msg.body)
            if not post_id_search:
                log.error('Failed to get post ID from watch offer message')
                return
            post_id = post_id_search.group(1)
            with self.uowm.start() as uow:
                existing_watch = uow.repostwatch.find_existing_watch(msg.dest.name, post_id)
                if existing_watch:
                    log.info('Existing watch found for post %s by user %s', post_id, msg.dest.name)
                    return
                uow.repostwatch.add(
                    RepostWatch(
                        post_id=post_id,
                        user=msg.dest.name,
                        source='Top Post'
                    )
                )
                uow.commit()
                log.info('Created post watch on %s for %s.  Source: Top Post', post_id, msg.author.name)
                msg.reply(WATCH_ENABLED)



    def _process_user_report(self, msg: Message):
        with self.uowm.start() as uow:
            existing = uow.user_report.get_first_by_message_id(msg.id)
            if existing:
                log.debug('Report %s has already been saved', msg.id)
                return

        report_data = self._load_msg_body_data(msg.body)
        if not report_data:
            log.info('Failed to get report data from message %s.  Not saving', msg.id)
            if len(self.failed_checks) > 10000:
                self.failed_checks = []
            if msg.id not in self.failed_checks:
                self.failed_checks.append(msg.id)
            return

        report = UserReport(
            post_id=report_data['post_id'],
            reported_by=msg.author.name,
            report_type=msg.subject,
            meme_template=report_data['meme_template'],
            msg_body=msg.body,
            message_id=msg.id,
            sent_for_voting=False
        )

        with self.uowm.start() as uow:
            uow.user_report.add(report)
            uow.commit()

        try:
            msg.reply('Thank you for your report. \n\nIt has been documented and will be reviewed further')
        except Exception as e:
            log.exception('Failed to send resposne to report.', exc_info=True)

    def _process_unknown_message(self, msg: Message) -> NoReturn:
        """
        Take an unknown message and forward to dev
        :param msg: Praw Message
        """
        dev = self.reddit.redditor('barrycarey')
        try:
            dev.message(f'FWD: {msg}', f'From {msg.author.name}\n\n{msg.body}')
            msg.reply(
                'Thank you for your message.  This inbox is not monitored.  I have forwarded your message to the developer')
        except Exception as e:
            log.exception('Failed to send message to dev', exc_info=True)

    def _load_msg_body_data(self, body: Text) -> Dict:
        """
        Attempt to load JSON data from provided message body
        :rtype: Dict
        :param body: String of data to load
        :return: Dict
        """
        try:
            return json.loads(body)
        except JSONDecodeError:
            log.error('Failed to load report data from body.  %s', body)

        opening = body.find('{')
        closing = body.find('}')
        if not opening and closing:
            log.error('Failed to find opening and closing brackets in: %s', body)
            return

        try:
            return json.loads(body[opening:closing + 1])
        except JSONDecodeError:
            log.error('Failed to load report data using opening and closing brackets')

if __name__ == '__main__':
    config = Config()
    uowm = SqlAlchemyUnitOfWorkManager(get_db_engine(config))
    reddit = get_reddit_instance(config)
    invite = InboxMonitor(uowm, reddit)
    while True:
        invite.check_inbox()