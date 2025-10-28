#!/usr/bin/env node
const { spawn } = require('child_process');
const inquirer = require('inquirer');

async function main() {
  const answers = await inquirer.prompt([
    {
      type: 'list',
      name: 'action',
      message: 'How do you want to open the app?',
      choices: [
        { name: 'Open in default browser (localhost:3000)', value: 'browser' },
        { name: 'Open in Chrome app window', value: 'chrome-app' },
        { name: 'Open in Edge app window', value: 'edge-app' },
        { name: 'Start dev server only (no auto-open)', value: 'none' }
      ]
    }
  ]);

  const dev = spawn('npm', ['run', 'start:dev'], { stdio: 'inherit', shell: true });

  if (answers.action === 'none') return;

  const url = 'http://localhost:3000';

  setTimeout(() => {
    if (answers.action === 'browser') {
      spawn('cmd', ['/c', 'start', '', url], { shell: true, detached: true });
      return;
    }
    if (answers.action === 'chrome-app') {
      const chrome = '"C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"';
      spawn(`${chrome} --app="${url}" --window-size=1100,800`, { shell: true, detached: true });
      return;
    }
    if (answers.action === 'edge-app') {
      const edge = '"C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe"';
      spawn(`${edge} --app="${url}" --window-size=1100,800`, { shell: true, detached: true });
      return;
    }
  }, 1500);
}

main().catch(err => { console.error(err); process.exit(1); });
