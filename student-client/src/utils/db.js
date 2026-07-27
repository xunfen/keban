const DB='keban_cache', VER=1
function open(){return new Promise((res,rej)=>{const r=indexedDB.open(DB,VER);r.onupgradeneeded=()=>{if(!r.result.objectStoreNames.contains('q'))r.result.createObjectStore('q',{keyPath:'id'})};r.onsuccess=()=>res(r.result);r.onerror=()=>rej(r.error)})}
export async function cacheQ(q){const db=await open();const tx=db.transaction('q','readwrite');tx.objectStore('q').put({...q,id:Date.now().toString()});return new Promise(r=>{tx.oncomplete=r})}
export async function getCached(){const db=await open();const tx=db.transaction('q','readonly');return new Promise(r=>{tx.objectStore('q').getAll().onsuccess=e=>r(e.target.result.reverse())})}
