export function preloadImages(urls: readonly string[], signal: AbortSignal): Promise<void> {
  return Promise.all(urls.map(url=>new Promise<void>((resolve,reject)=>{
    const image=new Image()
    let finished=false
    const cleanup=()=>{image.onload=null;image.onerror=null;signal.removeEventListener('abort',abort)}
    const finish=(error?: Error)=>{if(finished)return;finished=true;cleanup();if(error)reject(error);else resolve()}
    const abort=()=>{finish(new DOMException('Image preload aborted','AbortError'));image.src=''}
    if(signal.aborted) {abort();return}
    signal.addEventListener('abort',abort,{once:true})
    image.onload=()=>{void image.decode().then(()=>finish(),()=>finish(new Error('A startup image could not decode.')))}
    image.onerror=()=>finish(new Error('A startup image could not load.'))
    image.src=url
  }))).then(()=>{})
}
