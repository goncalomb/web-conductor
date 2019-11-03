package main

import (
	"net/http"
)

func limbo(w http.ResponseWriter, r *http.Request) {
	http.Error(w, "limbo", http.StatusNotFound)
}

func main() {
	http.ListenAndServe(":80", http.HandlerFunc(limbo))
}
