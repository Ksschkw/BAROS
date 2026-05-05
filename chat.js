const readline = require('readline');
const apiBase = process.env.COLOSSEUM_COPILOT_API_BASE;
const pat = process.env.COLOSSEUM_COPILOT_PAT;

if (!apiBase || !pat) {
  console.error('Environment variables not set. Run:');
  console.error('  setx COLOSSEUM_COPILOT_API_BASE "https://copilot.colosseum.com/api/v1"');
  console.error('  setx COLOSSEUM_COPILOT_PAT "your-token"');
  console.error('Then restart this terminal.');
  process.exit(1);
}

const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout,
  prompt: 'You: '
});

let conversationHistory = [];

async function askCopilot(question) {
  conversationHistory.push({ role: 'user', content: question });

  try {
    const response = await fetch(apiBase + '/chat/completions', {
      method: 'POST',
      headers: {
        'Authorization': 'Bearer ' + pat,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        messages: conversationHistory,
        stream: false,
      }),
    });

    if (!response.ok) {
      throw new Error('API error: ' + response.status);
    }

    const data = await response.json();
    const reply = data.choices?.[0]?.message?.content || 'No response content.';
    conversationHistory.push({ role: 'assistant', content: reply });
    return reply;
  } catch (err) {
    return 'Error: ' + err.message;
  }
}

console.log('=== Colosseum Copilot Chat ===');
console.log('Type your questions. Type "exit" to quit.\n');

function chat() {
  rl.prompt();
  rl.on('line', async (line) => {
    const input = line.trim();
    if (input.toLowerCase() === 'exit') {
      console.log('Goodbye!');
      rl.close();
      return;
    }
    if (!input) {
      rl.prompt();
      return;
    }

    console.log('Copilot is thinking...');
    const reply = await askCopilot(input);
    console.log('\nCopilot:', reply, '\n');
    rl.prompt();
  });
}

chat();