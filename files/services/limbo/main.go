package main

import (
	"io"
	"os"
	"encoding/json"
	"net/http"
	"net/http/httputil"
)

type logout_info struct {
	Auth bool `json:"auth"`
	Redirect string `json:"redirect"`
}

// using a non-authenticated route for '/logout' is required, specially on
// firefox where the a single '401 Unauthorized' from the backend is not enough
// to clear the session, with a non-authenticated route we can monitor the
// 'Authorization' header on the backend (not cleared by traefik) and do a
// redirect with a fake '__logout__' username to force the session to clear

const logout_script = `<!DOCTYPE html>
<body></body>
<script>
function logout({ auth, redirect }) {
	const nuke = new URL(window.location);
	nuke.username = '__logout__';
	nuke.password = Math.random().toString(36).substring(2);
	const [msg, url, time] = [
		['logged out, redirecting in 2 seconds...', redirect || window.location.origin, 2000],
		['logging out...', nuke, 1000],
	][auth ? 1 : 0];
	setTimeout(() => {
		document.body.innerHTML = '';
		window.location = url;
	}, time);
	document.body.appendChild(document.createElement('pre')).innerText = msg;
}
</script>
`

func limbo(w http.ResponseWriter, r *http.Request) {
	if r.URL.Path == "/logout" {
		logout_info_json, _ := json.Marshal(logout_info{
			Auth: r.Header.Get("Authorization") != "",
			Redirect: os.Getenv("LIMBO_LOGOUT_REDIRECT"),
		})
		w.Header().Set("Content-Type", "text/html; charset=utf-8")
		w.WriteHeader(http.StatusUnauthorized) // always 401 Unauthorized
		io.WriteString(w, logout_script)
		io.WriteString(w, "<script>logout(" + string(logout_info_json) + ");</script>")
		return
	}
	debug := os.Getenv("LIMBO_DEBUG")
	if (debug != "") {
		dump, _ := httputil.DumpRequest(r, true)
		http.Error(w, string(dump), http.StatusNotFound)
	} else {
		http.Error(w, "limbo", http.StatusNotFound)
	}
}

func main() {
	http.ListenAndServe(":80", http.HandlerFunc(limbo))
}
