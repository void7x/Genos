export function basename(path:string):string{const parts=path.split('/');return parts[parts.length-1]??path}
export function dirname(path:string):string{const parts=path.split('/');parts.pop();return parts.join('/')}
export function clockTime(iso:string):string{const d=new Date(iso);if(Number.isNaN(d.getTime()))return '';return d.toLocaleTimeString([],{hour:'2-digit',minute:'2-digit'})}
export function durationLabel(ms:number):string{if(ms<1000)return `${ms}ms`;return `${(ms/1000).toFixed(2)}s`}
export function percent(value:number):string{return `${Math.round(value*100)}%`}
export function plural(count:number,one:string,many=`${one}s`):string{return `${count} ${count===1?one:many}`}