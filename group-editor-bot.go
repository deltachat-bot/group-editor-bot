package main

import (
	"math/rand"
	"os"
	"path/filepath"
	"strconv"
	"strings"
	"time"

	"github.com/cavaliergopher/grab/v3"
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
			err = bot.Rpc.SetConfig(accId, "displayname", option.Some("Group Editor Bot"))
			if err != nil {
				cli.Logger.Error(err)
			}
			status := "I am a bot that helps managing editors in groups, send me /help for more info"
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
	selfAddr, err := bot.Rpc.GetConfig(accId, "addr")
	msg, err := bot.Rpc.GetMessage(accId, msgId)
	if err != nil {
		logger.Error(err)
		return
	}

	if msg.SystemMessageType == deltachat.SysmsgMemberAddedToGroup {
		resendPads(bot.Rpc, accId, msg.ChatId)
	}

	if msg.SystemMessageType == deltachat.SysmsgMemberRemovedFromGroup {
		if strings.Contains(msg.Text, "Member Me ("+*selfAddr.Value+") removed by ") {
			bot.Rpc.DeleteChat(accId, msg.ChatId)
		}
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
		case "/pin":
			sendMessage(bot.Rpc, accId, msg.ChatId, msg.Text)
			return
		case "/editor":
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

	if msg.Sender.Address != selfAddr.Unwrap() {
		err = bot.Rpc.DeleteMessages(accId, []deltachat.MsgId{msg.Id})
		if err != nil {
			logger.Error(err)
		} else {
			println("Deleted message " + strconv.FormatUint(uint64(msg.Id), 10))
		}
	}
}

func sendMessage(rpc *deltachat.Rpc, accId deltachat.AccountId, chatId deltachat.ChatId, command string) {
	var description string
	if len(command) > 7 {
		description = command[5:] // bot adds text after /pin as text for the pinned message
	} else {
		description = ""
	}
	msgID, err := rpc.SendMsg(accId, chatId, deltachat.MsgData{Text: description})
	if err != nil {
		cli.GetLogger(accId).With("chat", chatId).Error(err)
	}
	cli.Logger.Info("Sent pinned message " + string(msgID))
}

func sendPad(rpc *deltachat.Rpc, accId deltachat.AccountId, chatId deltachat.ChatId, command string) {
	HomeDir, err := os.UserHomeDir()
	editor_path := filepath.Join(HomeDir, ".config", "group-editor-bot", "durian-realtime-editor-v4.0.4.xdc")
	var description string
	if len(command) > 7 {
		description = command[8:] // bot adds text after /editor as description to the editor.xdc message
	} else {
		description = ""
	}
	msgID, err := rpc.SendMsg(accId, chatId, deltachat.MsgData{Text: description, File: editor_path})
	if err != nil {
		cli.GetLogger(accId).With("chat", chatId).Error(err)
	}
	cli.Logger.Info("Sent editor message " + string(msgID))
}

func resendPads(rpc *deltachat.Rpc, accId deltachat.AccountId, chatId deltachat.ChatId) {
	logger := cli.GetLogger(accId).With("chat", chatId)
	var toResend []deltachat.MsgId
	selfAddr, err := rpc.GetConfig(accId, "addr")
	if err == nil {
		msgIds, _ := rpc.GetMessageIds(accId, chatId, false, false)
		var msgIdStrings []string
		for i := range msgIds {
			msgIdStrings = append(msgIdStrings, strconv.FormatUint(uint64(msgIds[i]), 10))
		}
		// println("In this chat I know the messages: " + strings.Join(msgIdStrings, ","))
		for _, id := range msgIds {
			msg, _ := rpc.GetMessage(accId, id)
			senderaddress := msg.Sender.Address
			// println(strconv.FormatUint(uint64(msg.Id), 10) + senderaddress + selfAddr.Unwrap())
            // delete MemberAdded System Messages instead of trying to resend them; it will fail
            if msg.SystemMessageType == deltachat.SysmsgMemberAddedToGroup && msg.Sender.Address == selfAddr.Unwrap() {
                text := msg.Text
                err = rpc.DeleteMessages(accId, []deltachat.MsgId{msg.Id})
                if err != nil {
                    logger.Error(err)
                } else {
                    println("Deleted message " + strconv.FormatUint(uint64(msg.Id), 10) + ": " + text)
                }
                continue
            }
			if senderaddress == selfAddr.Unwrap() {
				toResend = append(toResend, id)
			}
		}
        // We wait here 5 seconds because otherwise the newly added member
        // might get the bot's messages before the member-added message
        // which breaks for the newly added member ("unable to verify sender")
        // This needs to be prevented on the chatmail core side but as of May 15 2025
        // this wait here makes it less likely the asynchronicity issue happens.
	    time.Sleep(5 * time.Second)
		if toResend != nil {
			err := rpc.ResendMessages(accId, toResend)
			for err != nil {
				var msgIdsStrings []string
				for i := range toResend {
					msgIdsStrings = append(msgIdsStrings, strconv.FormatUint(uint64(toResend[i]), 10))
				}
				cli.Logger.Error("Resending messages " + strings.Join(msgIdsStrings, ",") + " failed with error: '" + err.Error() + "'. Retrying.")
				r := rand.Intn(10)
				time.Sleep(time.Duration(r) * time.Second)
				err = rpc.ResendMessages(accId, toResend)
			}
		}
	}
}

func sendHelp(rpc *deltachat.Rpc, accId deltachat.AccountId, chatId deltachat.ChatId) {
	text := "I am a bot that manages editors in groups.\n\n"
	text += "To create a new shared editor for the group, you can write:\n\n"
	text += "/editor Shopping List for Friday's Example Party\n\n"
	text += "I will send an editor to the group, which anyone can edit; and if new members are added, they will see it, too."
	msgId, err := rpc.SendMsg(accId, chatId, deltachat.MsgData{Text: text})
	if err != nil {
		cli.GetLogger(accId).With("chat", chatId).Error(err)
	}
	time.Sleep(10 * time.Second) // sleep for 10 seconds, so the message has a chance to be sent
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
	msgId, err := rpc.SendMsg(accId, chatId, deltachat.MsgData{Text: qrdata, File: path})
	if err != nil {
		logger.Error(err)
	}
	time.Sleep(10 * time.Second) // sleep for 10 seconds, so the message has a chance to be sent
	err = rpc.DeleteMessages(accId, []deltachat.MsgId{msgId})
	if err != nil {
		cli.Logger.Error(err)
	}
}

func main() {
	cli.OnBotInit(onBotInit)

	HomeDir, err := os.UserHomeDir()
	DownloadDir := filepath.Join(HomeDir, ".config", "group-editor-bot")
	resp, err := grab.Get(DownloadDir, "https://apps.testrun.org/durian-realtime-editor-v4.0.4.xdc")
	if err != nil {
		cli.Logger.Error(err)
	}
	cli.Logger.Info("Download saved to ", resp.Filename)

	if err := cli.Start(); err != nil {
		cli.Logger.Error(err)
	}
}
