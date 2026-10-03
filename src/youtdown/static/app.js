const form = document.querySelector('#download-form');
const input = document.querySelector('#url');
const button = document.querySelector('#submit');
const result = document.querySelector('#result');
const status = document.querySelector('#status');
const save = document.querySelector('#save');

async function request(url, options) {
  const response = await fetch(url, { ...options, signal: AbortSignal.timeout(30000) });
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    const detail = body.detail;
    throw new Error(typeof detail === 'string' ? detail :
      Array.isArray(detail) ? detail.map(item => item.msg.replace(/^Value error, /, '')).join(' ') :
      `Não foi possível contactar o servidor (${response.status}).`);
  }
  return response.json();
}

form.addEventListener('submit', async event => {
  event.preventDefault();
  if (button.disabled) return;
  button.disabled = true;
  input.disabled = true;
  form.setAttribute('aria-busy', 'true');
  result.hidden = false;
  result.dataset.error = 'false';
  save.hidden = true;
  save.removeAttribute('href');
  status.textContent = 'A preparar o download…';
  try {
    let job = await request('/downloads', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url: input.value.trim(), format: 'audio' }),
    });
    while (job.status === 'queued' || job.status === 'running') {
      status.textContent = job.status === 'queued' ? 'O áudio está na fila…' :
        'A descarregar e converter o áudio em MP3. Mantém esta página aberta…';
      await new Promise(resolve => setTimeout(resolve, 1500));
      job = await request(`/downloads/${encodeURIComponent(job.job_id)}`);
    }
    if (job.status === 'failed') throw new Error(job.error || 'Não foi possível descarregar o áudio deste vídeo.');
    if (job.status !== 'done' || !job.filename) throw new Error('O servidor não devolveu o ficheiro MP3.');
    save.href = `/files/${job.filename.split('/').map(encodeURIComponent).join('/')}`;
    save.download = job.filename.split('/').pop();
    save.hidden = false;
    status.textContent = 'MP3 pronto! A transferência para o teu computador foi iniciada. Se não começar, usa o botão abaixo.';
    save.click();
  } catch (error) {
    result.dataset.error = 'true';
    status.textContent = error instanceof TypeError || error.name === 'TimeoutError' ?
      'Não foi possível contactar o servidor. Verifica a ligação e tenta novamente.' : error.message;
  } finally {
    button.disabled = false;
    input.disabled = false;
    form.removeAttribute('aria-busy');
  }
});
