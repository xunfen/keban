export function compressImage(file, maxW=800, q=.7) {
  return new Promise((res,rej)=>{
    const r=new FileReader()
    r.onload=e=>{
      const img=new Image()
      img.onload=()=>{
        const c=document.createElement('canvas')
        let {width:w,height:h}=img
        if(w>maxW){h=Math.round(h*maxW/w);w=maxW}
        c.width=w;c.height=h
        const ctx=c.getContext('2d');ctx.drawImage(img,0,0,w,h)
        c.toBlob(b=>res(b),'image/jpeg',q)
      }
      img.onerror=rej;img.src=e.target.result
    }
    r.onerror=rej;r.readAsDataURL(file)
  })
}
