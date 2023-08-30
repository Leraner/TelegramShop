import json
import logging
import typing

from aiogram import Bot, types
from aiogram.bot import api
from aiogram.types import base
from aiogram.utils.payload import prepare_arg, generate_payload, prepare_file
from aioredis import Redis


class CustomBotClient(Bot):
    def __init__(self, token: base.String, redis_cache: Redis):

        super().__init__(token)
        self.redis_cache = redis_cache

    async def set_cache(self, username: str, cache_key: str, cache: dict) -> None:
        await self.redis_cache.set(username + cache_key, json.dumps(cache, default=str))

    async def get_cache(self, username: str, cache_key: str) -> json:
        return json.loads(await self.redis_cache.get(username + cache_key))

    async def delete_message(self, chat_id: typing.Union[base.Integer, base.String],
                             message_id: base.Integer, for_cache: bool = False) -> base.Boolean:
        """
        for_cache - needs for deleting messages if user send command, not for deleting messages in switching pages
        """

        if not for_cache:
            username = (await self.get_chat(chat_id=chat_id)).username
            useless_messages = await self.get_cache(username=username, cache_key=':useless_messages')
            useless_messages.pop(useless_messages.index(message_id))
            await self.set_cache(username=username, cache_key=':useless_messages', cache=useless_messages)
            logging.info(f'MESSAGE {message_id} DELETED FROM {username} CACHE')
        await super().delete_message(chat_id=chat_id, message_id=message_id)

    async def send_photo(self,
                         chat_id: typing.Union[base.Integer, base.String],
                         photo: typing.Union[base.InputFile, base.String],
                         caption: typing.Optional[base.String] = None,
                         parse_mode: typing.Optional[base.String] = None,
                         caption_entities: typing.Optional[typing.List[types.MessageEntity]] = None,
                         message_thread_id: typing.Optional[base.Integer] = None,
                         disable_notification: typing.Optional[base.Boolean] = None,
                         protect_content: typing.Optional[base.Boolean] = None,
                         reply_to_message_id: typing.Optional[base.Integer] = None,
                         allow_sending_without_reply: typing.Optional[base.Boolean] = None,
                         reply_markup: typing.Union[types.InlineKeyboardMarkup,
                                                    types.ReplyKeyboardMarkup,
                                                    types.ReplyKeyboardRemove,
                                                    types.ForceReply, None] = None,
                         has_spoiler: typing.Optional[base.Boolean] = None,
                         ) -> types.Message:
        reply_markup = prepare_arg(reply_markup)
        caption_entities = prepare_arg(caption_entities)
        payload = generate_payload(**locals(), exclude=['photo'])
        if self.parse_mode and caption_entities is None:
            payload.setdefault('parse_mode', self.parse_mode)
        if self.protect_content is not None:
            payload.setdefault('protect_content', self.protect_content)

        files = {}
        prepare_file(payload, files, 'photo', photo)

        result = await self.request(api.Methods.SEND_PHOTO, payload, files)
        message_with_photo = types.Message(**result)

        # Add into cache bot's messages
        username = (await self.get_chat(chat_id=chat_id)).username
        useless_messages = await self.get_cache(username=username, cache_key=':useless_messages')
        useless_messages.append(message_with_photo.message_id)
        await self.set_cache(username=username, cache_key=':useless_messages', cache=useless_messages)
        logging.info(f'ADDED MESSAGE(PHOTO) {message_with_photo.message_id} INTO {username} CACHE')

        return message_with_photo

    async def send_message(self,
                           chat_id: typing.Union[base.Integer, base.String],
                           text: base.String,
                           parse_mode: typing.Optional[base.String] = None,
                           entities: typing.Optional[typing.List[types.MessageEntity]] = None,
                           disable_web_page_preview: typing.Optional[base.Boolean] = None,
                           message_thread_id: typing.Optional[base.Integer] = None,
                           disable_notification: typing.Optional[base.Boolean] = None,
                           protect_content: typing.Optional[base.Boolean] = None,
                           reply_to_message_id: typing.Optional[base.Integer] = None,
                           allow_sending_without_reply: typing.Optional[base.Boolean] = None,
                           reply_markup: typing.Union[types.InlineKeyboardMarkup,
                                                      types.ReplyKeyboardMarkup,
                                                      types.ReplyKeyboardRemove,
                                                      types.ForceReply, None] = None,
                           ) -> types.Message:

        reply_markup = prepare_arg(reply_markup)
        entities = prepare_arg(entities)
        payload = generate_payload(**locals())
        if self.parse_mode and entities is None:
            payload.setdefault('parse_mode', self.parse_mode)
        if self.disable_web_page_preview:
            payload.setdefault('disable_web_page_preview', self.disable_web_page_preview)
        if self.protect_content is not None:
            payload.setdefault('protect_content', self.protect_content)

        result = await self.request(api.Methods.SEND_MESSAGE, payload)
        message = types.Message(**result)

        # Add into cache bot's messages
        username = (await self.get_chat(chat_id=chat_id)).username
        useless_messages = await self.get_cache(username=username, cache_key=':useless_messages')
        useless_messages.append(message.message_id)
        await self.set_cache(username=username, cache_key=':useless_messages', cache=useless_messages)
        logging.info(f'ADDED MESSAGE(SIMPLE MESSAGE) {message.message_id} INTO {username} CACHE')

        return message
