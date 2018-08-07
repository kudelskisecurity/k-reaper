package main

import (
	"fmt"
	"log"
	"os"
	"strings"

	"golang.org/x/crypto/ssh"
)

func main() {
	in := []byte(os.Args[1])
	key, _, _, rest, err := ssh.ParseAuthorizedKey(in)
	if err != nil {
		log.Fatal(err)
	}
	if len(rest) > 0 {
		log.Fatalf("rest: got %q, want empty", rest)

	}
	cert, ok := key.(*ssh.Certificate)
	if !ok {
		log.Fatalf("got %v (%T), want *Certificate", key, key)

	}

	new := string(ssh.MarshalAuthorizedKey(cert.Key))
	new2 := string(ssh.MarshalAuthorizedKey(cert.SignatureKey))

	fmt.Printf("%v", new)
	fmt.Printf("%v", new2)
	fmt.Println(strings.Join(cert.ValidPrincipals, ";"))
	fmt.Println(cert.ValidAfter)
	fmt.Println(cert.ValidBefore)
}
