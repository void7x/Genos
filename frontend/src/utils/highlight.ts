export interface Token{type:'kw'|'str'|'num'|'com'|'fn'|'cls'|'op'|'plain'|'diff-add'|'diff-del';value:string}
const PY_KEYWORDS=new Set(['def','return','if','elif','else','for','while','in','not','and','or','import','from','as','class','try','except','finally','raise','with','lambda','yield','pass','break','continue','None','True','False','assert','global','nonlocal','async','await','is','del'])
const RULES:{re:RegExp;type:Token['type']}[]=[
{re:/^#[^\n]*/,type:'com'},
{re:/^("""[\s\S]*?"""|'''[\s\S]*?'''|"(?:[^"\\\n]|\\.)*"|'(?:[^'\\\n]|\\.)*')/,type:'str'},
{re:/^\b\d+(?:\.\d+)?\b/,type:'num'},
{re:/^[A-Za-z_]\w*(?=\s*\()/,type:'fn'},
{re:/^\b[A-Z][A-Za-z0-9_]*\b/,type:'cls'},
{re:/^[A-Za-z_]\w*/,type:'plain'},
{re:/^(==|!=|<=|>=|->|::|[+\-*/%=<>!&|^~])/,type:'op'},
{re:/^\s+/,type:'plain'},
{re:/^[^\sA-Za-z_]/,type:'plain'}]
export function tokenizeLine(line:string,language='python'):Token[]{if(language==='text'||language==='diff')return[{type:'plain',value:line}];if(/^\+\+\+|^---|^@@/.test(line))return[{type:line.startsWith('@@')?'op':line.startsWith('+')?'diff-add':'diff-del',value:line}];const tokens:Token[]=[];let rest=line;while(rest.length>0){let matched=false;for(const rule of RULES){const m=rule.re.exec(rest);if(!m)continue;const value=m[0];const type=rule.type==='plain'&&PY_KEYWORDS.has(value)?'kw':rule.type;tokens.push({type,value});rest=rest.slice(value.length);matched=true;break}if(!matched){tokens.push({type:'plain',value:rest[0]});rest=rest.slice(1)}}return tokens}
export const TOKEN_CLASS:Record<Token['type'],string|null>={kw:'tok-kw',str:'tok-str',num:'tok-num',com:'tok-com',fn:'tok-fn',cls:'tok-cls',op:'tok-op',plain:null,'diff-add':'tok-diff-add','diff-del':'tok-diff-del'}
