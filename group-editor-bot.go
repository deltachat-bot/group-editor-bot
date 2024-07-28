package main

import (
	"os"
	"path/filepath"
	"strings"

	"github.com/deltachat-bot/deltabot-cli-go/botcli"
	"github.com/deltachat/deltachat-rpc-client-go/deltachat"
	"github.com/deltachat/deltachat-rpc-client-go/deltachat/option"
	qrcode "github.com/skip2/go-qrcode"
	"github.com/spf13/cobra"
)

var cli = botcli.New("group-editor-bot")

func onBotInit(cli *botcli.BotCli, bot *deltachat.Bot, cmd *cobra.Command, args []string) {
	bot.OnNewMsg(onNewMsg)

	accounts, err := bot.Rpc.GetAllAccountIds()
	if err != nil {
		cli.Logger.Error(err)
	}
	for _, accId := range accounts {
		name, err := bot.Rpc.GetConfig(accId, "displayname")
		if err != nil {
			cli.Logger.Error(err)
		}
		if name.UnwrapOr("") == "" {
			err = bot.Rpc.SetConfig(accId, "displayname", option.Some("InviteBot"))
			if err != nil {
				cli.Logger.Error(err)
			}
			status := "I am a bot that helps you invite friends to your private groups, send me /help for more info"
			err = bot.Rpc.SetConfig(accId, "selfstatus", option.Some(status))
			if err != nil {
				cli.Logger.Error(err)
			}
			err = bot.Rpc.SetConfig(accId, "delete_server_after", option.Some("1"))
			if err != nil {
				cli.Logger.Error(err)
			}
		}
	}
}

func onNewMsg(bot *deltachat.Bot, accId deltachat.AccountId, msgId deltachat.MsgId) {
	logger := cli.GetLogger(accId).With("msg", msgId)
	msg, err := bot.Rpc.GetMessage(accId, msgId)
	if err != nil {
		logger.Error(err)
		return
	}

	if msg.SystemMessageType == deltachat.SysmsgMemberAddedToGroup {
		resendPads(bot.Rpc, accId, msg.ChatId)
	}

	if !msg.IsBot && !msg.IsInfo && msg.FromId > deltachat.ContactLastSpecial {
		chat, err := bot.Rpc.GetBasicChatInfo(accId, msg.ChatId)
		if err != nil {
			logger.Error(err)
			return
		}
		if chat.ChatType == deltachat.ChatSingle || strings.HasPrefix(msg.Text, "/") {
			err = bot.Rpc.MarkseenMsgs(accId, []deltachat.MsgId{msg.Id})
			if err != nil {
				logger.Error(err)
			}
		}

		args := strings.Split(msg.Text, " ")
		switch args[0] {
		case "/invite":
			if chat.ChatType == deltachat.ChatGroup {
				sendInviteQr(bot.Rpc, accId, msg.ChatId)
			} else {
				text := "The /invite command can only be used in groups, send /help for more info"
				_, err := bot.Rpc.SendMsg(accId, msg.ChatId, deltachat.MsgData{Text: text})
				if err != nil {
					logger.Error(err)
				}
			}
		case "/pad":
			sendPad(bot.Rpc, accId, msg.ChatId, msg.Text)
			return
		case "/help":
			sendHelp(bot.Rpc, accId, msg.ChatId)
		default:
			if chat.ChatType == deltachat.ChatSingle {
				sendHelp(bot.Rpc, accId, msg.ChatId)
			}
		}
	}

	err = bot.Rpc.DeleteMessages(accId, []deltachat.MsgId{msg.Id})
	if err != nil {
		logger.Error(err)
	}
}

func sendPad(rpc *deltachat.Rpc, accId deltachat.AccountId, chatId deltachat.ChatId, command string) {
	editor_path := "editor.xdc"
	var description string
	if len(command) > 4 {
		description = command[5:] // bot adds text after /pad as description to the editor.xdc message
	} else {
		description = ""
	}
	_, err := rpc.SendMsg(accId, chatId, deltachat.MsgData{Text: description, File: editor_path})
	if err != nil {
		cli.GetLogger(accId).With("chat", chatId).Error(err)
	}
}

func resendPads(rpc *deltachat.Rpc, accId deltachat.AccountId, chatId deltachat.ChatId) {
	var toResend []deltachat.MsgId
	selfAddr, err := rpc.GetConfig(accId, "addr")
	if err == nil {
		msgIds, _ := rpc.GetMessageIds(accId, chatId, false, false)
		for _, id := range msgIds {
			msg, _ := rpc.GetMessage(accId, id)
			senderaddress := msg.Sender.Address
			if senderaddress == selfAddr.Unwrap() && msg.WebxdcInfo != nil {
				toResend = append(toResend, id)
			}
		}
		err := rpc.ResendMessages(accId, toResend)
		if err != nil {
			cli.Logger.Error("Resending messages failed.")
		}
	}
}

func sendHelp(rpc *deltachat.Rpc, accId deltachat.AccountId, chatId deltachat.ChatId) {
	text := "I am a bot that manages editors in groups.\n\n"
	text += "To create a new shared editor for the group, you can write:\n\n"
	text += "/pad Shopping List for Friday's Example Party\n\n"
	text += "I will send an editor to the group, which anyone can edit; and if new members are added, they will see it, too."
	msgId, err := rpc.SendMsg(accId, chatId, deltachat.MsgData{Text: text})
	if err != nil {
		cli.GetLogger(accId).With("chat", chatId).Error(err)
	}
	err = rpc.DeleteMessages(accId, []deltachat.MsgId{msgId})
	if err != nil {
		cli.Logger.Error(err)
	}

}

func sendInviteQr(rpc *deltachat.Rpc, accId deltachat.AccountId, chatId deltachat.ChatId) {
	logger := cli.GetLogger(accId).With("chat", chatId)
	qrdata, _, err := rpc.GetChatSecurejoinQrCodeSvg(accId, option.Some(chatId))
	if err != nil {
		logger.Error(err)
		return
	}

	dir, err := os.MkdirTemp("", "")
	if err != nil {
		logger.Error(err)
		return
	}
	defer os.RemoveAll(dir)
	path := filepath.Join(dir, "qr.png")

	err = qrcode.WriteFile(qrdata, qrcode.Medium, 256, path)
	if err != nil {
		logger.Error(err)
		return
	}
	_, err = rpc.SendMsg(accId, chatId, deltachat.MsgData{Text: botcli.GenerateInviteLink(qrdata), File: path})
	if err != nil {
		logger.Error(err)
	}
}

func main() {
	cli.OnBotInit(onBotInit)
	if err := cli.Start(); err != nil {
		cli.Logger.Error(err)
	}
}
