package main

import (
	"os"
	"net/http"
	"net/http/httputil"
)

func limbo(w http.ResponseWriter, r *http.Request) {
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
