#!/usr/bin/python3
# -*- coding: utf-8 -*-

from telegram.ext import Updater
from telegram.ext import CommandHandler
from telegram.ext import MessageHandler
from telegram.ext import Filters
from telegram import ParseMode

import json
import os
import logging

PATH = os.path.dirname(os.path.realpath(__file__))
TOKEN = open(os.path.join(PATH, "token.txt")).read().strip()


def start(bot, update):
    bot.send_message(chat_id=update.message.chat_id, text="Hallo, ich bin die Leseliste. Schick mir den /help befehl um mehr zu lernen.")


def read_list(chat_id):
    filename = os.path.join(PATH, "lists", str(chat_id)+".json")
    # read filecontents if already exists
    if os.path.isfile(filename):
        with open(filename) as f:
            liste = json.load(f)
    else:
        liste = {"buecher": {}, "artikel": {}}
    return liste


def save_list(liste, id):
    filename = os.path.join(PATH, "lists", str(id)+".json")
    with open(filename, "w") as f:
        json.dump(liste, f, sort_keys=True, indent=4)


def add(chat_id, typ, args):
    leseliste = read_list(chat_id)
    name = " ".join(args)
    key = create_key(args, leseliste[typ])
    leseliste[typ][key] = {"name": name, "key": key, "read": False}

    save_list(leseliste, chat_id)


def create_key(args, liste):
    candidates = [a for a in args if len(a)>2][:3]
    if candidates == []:
        return "".join(args[:3])
    key = ""
    for c in candidates:
        key += c[:2]
    if not key in liste:
        return key
    counter = 1
    while key+str(counter) in liste:
        counter += 1
    return key+str(counter)


def add_book(bot, update, args):
    # if no arguments were given
    if len(args)==0:
        bot.send_message(chat_id=update.message.chat_id, text="Benutze diesen Befehl so: /addbook Titel, Autor, wasauchimmer ...")
        return
    add(update.message.chat_id, "buecher", args)
    bot.send_message(chat_id=update.message.chat_id, text="ok, habs aufgeschrieben. /list")


def add_article(bot, update, args):
    # if no arguments were given
    if len(args)==0:
        bot.send_message(chat_id=update.message.chat_id, text="Benutze diesen Befehl so: /addarticle Titel, Autor, wasauchimmer ...")
        return
    add(update.message.chat_id, "artikel", args)
    bot.send_message(chat_id=update.message.chat_id, text="ok, habs aufgeschrieben. /list")


def list_all(bot, update):
    liste = read_list(update.message.chat_id)
    def composeprettylist(l):
        composed = ""
        for item in l:
            prefix = "✅" if l[item]["read"] else "📖"
            composed += "{}`[{}]` {}\n".format(prefix, item, l[item]["name"])
        return composed

    message = ""
    buecher = composeprettylist(liste["buecher"])
    artikel = composeprettylist(liste["artikel"])
    if not buecher == "":
        buecher = "*Bücher*\n" + buecher
    if not artikel == "":
        artikel = "*Artikel*\n" + artikel
    message = buecher + artikel
    if message == "":
        message = "Grad sind keine Sachen auf der Leseliste."
    else:
        message = "*Die Leseliste*\n\n" + message

    bot.send_message(chat_id=update.message.chat_id, text=message, parse_mode=ParseMode.MARKDOWN)


def mark_as_read(bot, update, args):
    # if no arguments were given
    if len(args)==0:
        bot.send_message(chat_id=update.message.chat_id, text="Benutze diesen Befehl so: /markasread key\nDen key findest du mit /list raus, der steht zwischen den eckigen Klammern.")
        return

    liste = read_list(update.message.chat_id)
    if args[0] in liste["buecher"]:
        liste["buecher"][args[0]]["read"] = True
    elif args[0] in liste["artikel"]:
        liste["artikel"][args[0]]["read"] = True
    else:
        bot.send_message(chat_id=update.message.chat_id,
            text="Ich konnte keinen Eintrag mit dem Key `{}` finden...".format(args[0]),
            parse_mode=ParseMode.MARKDOWN)
        return
    save_list(liste, update.message.chat_id)
    bot.send_message(chat_id=update.message.chat_id,
            text="ok, hab mir gemerkt dass du `{}` gelesen hast.".format(args[0]),
            parse_mode=ParseMode.MARKDOWN)


def remove(bot, update, args):
    # if no arguments were given
    if not len(args)==1:
        bot.send_message(chat_id=update.message.chat_id, text="Benutze diesen Befehl so: /remove key\nDen key findest du mit /list raus, der steht zwischen den eckigen Klammern.")
        return

    liste = read_list(update.message.chat_id)
    deleted = liste["buecher"].pop(args[0], None)
    if not deleted:
        deleted = liste["artikel"].pop(args[0], None)
    if not deleted:
        bot.send_message(chat_id=update.message.chat_id,
            text="Hab keinen Eintrag mit diesem Key gefunden...")
        return

    save_list(liste, update.message.chat_id)
    bot.send_message(chat_id=update.message.chat_id,
        text="Ok, hab {} von der Liste runter.".format(deleted["name"]))


def resetlist(bot, update):
    filename = os.path.join(PATH, "lists", str(update.message.chat_id)+".json")
    # read filecontents if already exists
    if os.path.isfile(filename):
        os.remove(filename)
        bot.send_message(chat_id=update.message.chat_id,
            text="Ok, hab alles gelöscht.")
    else:
        bot.send_message(chat_id=update.message.chat_id,
            text="Hab eh keine Liste!")


def help(bot, update):
    help_templatefile = os.path.join(PATH, "help.txt")
    with open(help_templatefile) as f:
        message = f.read()
    bot.send_message(chat_id=update.message.chat_id, text=message,
        parse_mode=ParseMode.MARKDOWN)


# to be fired on unknown commands
def unknown(bot, update):
    message = "Den befehl kenn ich nicht! 😱\nnimm den /help befehl um mehr zu erfahren"
    bot.send_message(chat_id=update.message.chat_id, text=message)


def main():
    # setup logging info
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                     level=logging.INFO)
    logger = logging.getLogger(__name__)
    # bot itself
    updater = Updater(token=TOKEN)
    dispatcher = updater.dispatcher

    start_handler = CommandHandler("start", start)
    dispatcher.add_handler(start_handler)
    addbook_handler = CommandHandler("add", add_book, pass_args=True)
    dispatcher.add_handler(addbook_handler)
    addarticle_handler = CommandHandler("addarticle", add_article, pass_args=True)
    dispatcher.add_handler(addarticle_handler)
    listall_handler = CommandHandler("list", list_all)
    dispatcher.add_handler(listall_handler)
    markasread_handler = CommandHandler("markasread", mark_as_read, pass_args=True)
    dispatcher.add_handler(markasread_handler)
    remove_handler = CommandHandler("remove", remove, pass_args=True)
    dispatcher.add_handler(remove_handler)
    resetlist_handler = CommandHandler("resetlist", resetlist)
    dispatcher.add_handler(resetlist_handler)
    help_handler = CommandHandler('help', help)
    dispatcher.add_handler(help_handler)

    unknown_handler = MessageHandler(Filters.command, unknown)
    dispatcher.add_handler(unknown_handler)

    updater.start_polling()
    updater.idle()


if __name__=="__main__":
    main()
