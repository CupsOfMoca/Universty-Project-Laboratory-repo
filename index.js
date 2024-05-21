const { Client, GatewayIntentBits, Events} = require("discord.js");
const { joinVoiceChannel } = require("@discordjs/voice");
const { leaveVoiceChannel } = require("@discordjs/voice");
const { addSpeechEvent, SpeechEvents } = require("discord-speech-recognition");

const client = new Client({
  intents: [
    GatewayIntentBits.GuildVoiceStates,
    GatewayIntentBits.GuildMessages,
    GatewayIntentBits.Guilds,
    GatewayIntentBits.MessageContent,
  ],
});
addSpeechEvent(client);
var chat;
var voiceConn; // Declare a variable to hold the voice connection

client.on(Events.MessageCreate, async (msg) => {
  const voiceChannel = msg.member?.voice.channel;
  chat = msg.channel;
  console.log(msg.content); 
  if (voiceChannel && msg.content.includes("@1211329150556835860")) {
    if(msg.content.includes("join")){
      voiceConn = await joinVoiceChannel({
        channelId: voiceChannel.id,
        guildId: voiceChannel.guild.id,
        adapterCreator: voiceChannel.guild.voiceAdapterCreator,
        selfDeaf: false,
      });
    } 
    else if( msg.content.includes("leave") && voiceConn){
      await voiceConn.destroy(); // Disconnect from the voice channel
      voiceConn = null; // Reset the voice connection variable
    }
    
  }
  else if( msg.content.toLowerCase().includes("answer")&& msg.content.includes("@1211329150556835860")){
    cleanedMessage=msg.content.replace("<@1211329150556835860>","").replace("answer this: ","");
    console.log(cleanedMessage)
    chat.send(`<@${msg.author.id}>\n`+await sendToChainlit(cleanedMessage));
  }
  else if(msg.content.includes("kurva anyád") ||msg.content.includes("hülye bot") ||msg.content.includes("baszdmeg")||msg.content.includes("bazdmeg")){
    var basszameg = `<@${msg.author.id}> akkor a kurva anyád`;
    if(!basszameg.includes("@1211329150556835860")){
      
      chat.send( basszameg)
    } 
  }
});


async function sendToChainlit(message) {
  const url = "http://127.0.0.1:5000/discord";

  try {
    const response = await fetch(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ message: message }),
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`Network response was not ok: ${errorText}`);
    }

    const data = await response.json();
    console.log('Response:', data);
    return data;
  } catch (error) {
    console.error('There was a problem with your fetch operation:', error);
  }
  
}



client.on(SpeechEvents.speech, async (msg) => {
  // If bot didn't recognize speech, content will be empty
  if (!msg.content) return;
  console.log(msg.content);
  if(msg.content.includes("Bashi") || msg.content.includes("buzzy") || msg.content.includes("bushy")){
    try {
      const message = `<@${msg.author.id}>`+await sendToChainlit(msg.content);
      if (message) {
        chat.send(message);
      } else {
        chat.send("An error occurred, sorry!");
      }
    } catch (error) {
      console.error('There was a problem processing speech:', error);
      chat.send("An error occurred, sorry!");
    }
  }
  
});


client.on(Events.ClientReady, () => {
  console.log("Ready!");
});

client.login("");