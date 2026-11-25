// Cloudflare Pages Function för /api/sl. Själva logiken finns i lib/sl.mjs.
import { handle } from "../../lib/sl.mjs";
export const onRequest = ({ request, env }) => handle(request, env);
