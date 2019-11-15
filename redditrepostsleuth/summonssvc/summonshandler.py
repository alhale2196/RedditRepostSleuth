import re
import time
from datetime import datetime
from typing import Tuple, Text

from praw.exceptions import APIException

from redditrepostsleuth.core.config import Config
from redditrepostsleuth.core.db.databasemodels import Summons, Post
from redditrepostsleuth.core.db.uow.unitofworkmanager import UnitOfWorkManager
from redditrepostsleuth.core.duplicateimageservice import DuplicateImageService
from redditrepostsleuth.core.exception import NoIndexException
from redditrepostsleuth.core.logging import log
from redditrepostsleuth.core.model.comment_reply import CommentReply
from redditrepostsleuth.core.model.events.influxevent import InfluxEvent
from redditrepostsleuth.core.model.events.summonsevent import SummonsEvent
from redditrepostsleuth.core.model.repostresponse import RepostResponseBase
from redditrepostsleuth.core.services.responsebuilder import ResponseBuilder
from redditrepostsleuth.core.services.eventlogging import EventLogging
from redditrepostsleuth.core.services.reddit_manager import RedditManager
from redditrepostsleuth.core.services.response_handler import ResponseHandler
from redditrepostsleuth.core.util.constants import NO_LINK_SUBREDDITS
from redditrepostsleuth.core.util.helpers import build_markdown_list, build_msg_values_from_search, create_first_seen, \
    searched_post_str
from redditrepostsleuth.core.util.objectmapping import submission_to_post
from redditrepostsleuth.core.util.replytemplates import UNSUPPORTED_POST_TYPE, UNKNOWN_COMMAND, LINK_ALL, \
    REPOST_NO_RESULT, DEFAULT_COMMENT_OC, \
    IMAGE_REPOST_ALL
from redditrepostsleuth.core.util.reposthelpers import check_link_repost
from redditrepostsleuth.ingestsvc.util import pre_process_post
from redditrepostsleuth.summonssvc.commandparsing.command_parser import CommandParser


class SummonsHandler:
    def __init__(
            self,
            uowm: UnitOfWorkManager,
            image_service: DuplicateImageService,
            reddit: RedditManager,
            response_builder: ResponseBuilder,
            response_handler: ResponseHandler,
            config: Config = None,
            event_logger: EventLogging = None,
            summons_disabled=False
    ):
        self.uowm = uowm
        self.image_service = image_service
        self.reddit = reddit
        self.summons_disabled = summons_disabled
        self.response_builder = response_builder
        self.response_handler = response_handler
        self.event_logger = event_logger
        self.config = config or Config()
        self.command_parser = CommandParser()


    def handle_summons(self):
        """
        Continually check the summons table for new requests.  Handle them as they are found
        """
        while True:
            try:
                with self.uowm.start() as uow:
                    summons = uow.summons.get_unreplied()
                    for s in summons:
                        self.handle_repost_request(s)
                        summons_event = SummonsEvent((datetime.utcnow() - s.summons_received_at).seconds, s.summons_received_at, s.requestor, event_type='summons')
                        self._send_event(summons_event)
                time.sleep(2)
            except Exception as e:
                log.exception('Exception in handle summons thread')

    def handle_summons(self, summons: Summons):
        base_command = self.command_parser

    def _strip_summons_flags(self, comment_body: Text) -> Text:
        log.debug('Attempting to parse summons comment')
        log.debug(comment_body)
        user_tag = comment_body.lower().find('repostsleuthbot')
        keyword_tag = comment_body.lower().find('?repost')
        if user_tag < 1 and keyword_tag < 1:
            log.error('Unable to find summons tag in: %s', comment_body)
            return

    def handle_repost_request(self, summons: Summons):

        with self.uowm.start() as uow:
            post = uow.posts.get_by_post_id(summons.post_id)

        response = RepostResponseBase(summons_id=summons.id)

        if not post:
            post = self.save_unknown_post(summons.post_id)

        if not post:
            response.message = 'Sorry, I\'m having trouble with this post. Please try again later'
            log.info('Failed to ingest post %s.  Sending error response', summons.post_id)
            self._send_response(summons.comment_id, response)
            return

        # TODO - Send PM instead of comment reply
        if self.summons_disabled:
            log.info('Sending summons disabled message')
            response.message = 'I\m currently down for maintenance, check back in an hour'
            self._send_response(summons.comment_id, response)
            return

        if post.post_type is None or post.post_type not in config.supported_post_types:
            log.error('Submission has no post hint.  Cannot process summons')
            response.status = 'error'
            response.message = UNSUPPORTED_POST_TYPE
            self._send_response(summons.comment_id, response)
            return

        # We just got the summons flag without a command.  Default to repost check
        if not parsed_command:
            self.process_repost_request(summons, post)
            return

        sub_command = parsed_command.group('subcommand')
        if sub_command:
            sub_command = sub_command.strip()

        # TODO handle case when no command is passed
        if parsed_command.group('command').lower() == 'check':
            self.process_repost_request(summons, post, sub_command=sub_command)
        else:
            log.error('Unknown command')
            response.message = UNKNOWN_COMMAND
            self._send_response(summons.comment_id, response)


    def process_repost_request(self, summons: Summons, post: Post, sub_command: str = None):
        if post.post_type == 'image':
            self.process_image_repost_request(summons, post, sub_command=sub_command)
        elif post.post_type == 'link':
            self.process_link_repost_request(summons, post, sub_command=sub_command)

    def process_link_repost_request(self, summons: Summons, post: Post, sub_command: str = None):

        response = RepostResponseBase(summons_id=summons.id)
        with self.uowm.start() as uow:
            search_count = (uow.posts.get_newest_post()).id
            result = check_link_repost(post, self.uowm)
            if len(result.matches) > 0:
                response.message = LINK_ALL.format(occurrences=len(result.matches),
                                                   searched=search_count,
                                                   original_href='https://reddit.com' + result.matches[0].perma_link,
                                                   link_text=result.matches[0].perma_link)
            else:
                response.message = REPOST_NO_RESULT.format(total=search_count)
            self._send_response(summons.comment_id, response)

    def process_image_repost_request(self, summons: Summons, post: Post, sub_command: str = None):

        response = RepostResponseBase(summons_id=summons.id)

        target_hamming_distance, target_annoy_distance = self._get_target_distances(post.subreddit)

        try:
            search_results = self.image_service.check_duplicates_wrapped(
                post,
                target_annoy_distance=target_annoy_distance,
                target_hamming_distance=target_hamming_distance,
                meme_filter=True
            )
        except NoIndexException:
            log.error('No available index for image repost check.  Trying again later')
            time.sleep(10)
            return

        msg_values = msg_values = build_msg_values_from_search(search_results, self.uowm)

        if not search_results.matches:
            response.message = self.response_builder.build_default_oc_comment(msg_values)
        else:

            if sub_command == 'all':
                response.message = IMAGE_REPOST_ALL.format(
                    count=len(search_results.matches),
                    searched_posts=searched_post_str(post, search_results.index_size),
                    firstseen=create_first_seen(search_results.matches[0].post, summons.subreddit),
                    time=search_results.total_search_time

                )
                response.message = response.message + build_markdown_list(search_results.matches)
                if len(search_results.matches) > 4:
                    log.info('Sending check all results via PM with %s matches', len(search_results.matches))
                    comment = self.reddit.comment(summons.comment_id)
                    self.response_handler.send_private_message(comment.author, response.message)
                    response.message = f'I found {len(search_results.matches)} matches.  I\'m sending them to you via PM to reduce comment spam'

                response.message = response.message
            else:

                response.message = self.response_builder.build_sub_repost_comment(post.subreddit, msg_values)

        self._send_response(summons.comment_id, response, no_link=post.subreddit in NO_LINK_SUBREDDITS)

    def _get_target_distances(self, subreddit: str) -> Tuple[int, float]:
        """
        Check if the post we were summoned on is in a monitored sub.  If it is get the target distances for that sub
        :rtype: Tuple[int,float]
        :param subreddit: Subreddit name
        :return: Tuple with target hamming and annoy
        """
        with self.uowm.start() as uow:
            monitored_sub = uow.monitored_sub.get_by_sub(subreddit)
            if monitored_sub:
                return monitored_sub.target_hamming, monitored_sub.target_annoy
            return self.config.default_hamming_distance, self.config.default_annoy_distance

    def _send_response(self, comment_id: str, response: RepostResponseBase, no_link=False):
        log.debug('Sending response to summons comment %s. MESSAGE: %s', comment_id, response.message)
        try:
            reply = self.response_handler.reply_to_comment(comment_id, response.message, source='summons', send_pm_on_fail=True)
        except APIException as e:
            return
        response.message = reply.body # TODO - I don't like this.  Make save_resposne take a CommentReply
        self._save_response(response, reply)

    def _save_response(self, response: RepostResponseBase, reply: CommentReply, subreddit: str = None):
        with self.uowm.start() as uow:
            summons = uow.summons.get_by_id(response.summons_id)
            if summons:
                summons.comment_reply = response.message
                summons.summons_replied_at = datetime.utcnow()
                summons.comment_reply_id = reply.comment.id if reply.comment else None # TODO: Hacky
                uow.commit()
                log.debug('Committed summons response to database')

    def _save_post(self, post: Post):
        with self.uowm.start() as uow:
            uow.posts.update(post)
            uow.commit()

    def save_unknown_post(self, post_id: str) -> Post:
        """
        If we received a request on a post we haven't ingest save it
        :param submission: Reddit Submission
        :return:
        """
        submission = self.reddit.submission(post_id)
        post = pre_process_post(submission_to_post(submission), self.uowm, None)
        if not post or post.post_type != 'image':
            log.error('Problem ingesting post.  Either failed to save or it is not an image')
            return

        return post

    def _send_event(self, event: InfluxEvent):
        if self.event_logger:
            self.event_logger.save_event(event)