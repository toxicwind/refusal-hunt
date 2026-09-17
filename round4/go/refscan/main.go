package main
import (
	"bufio"
	"crypto/md5"
	"encoding/hex"
	"encoding/json"
	"flag"
	"fmt"
	"os"
	"sync"
)
const canned = "b4aefd29108f232f9c0d5a4b030215c1"
type In struct {
	ID   int    `json:"id"`
	Body string `json:"body"`
}
type Out struct {
	ID    int    `json:"id"`
	MD5   string `json:"md5"`
	Class string `json:"class"`
}
func classify(body, sum string) string {
	if sum == canned {
		return "refused_canned"
	}
	if body == "pong" {
		return "pong_genuine"
	}
	return "unknown"
}
func main() {
	workers := flag.Int("workers", 4, "hash workers")
	flag.Parse()
	in := make(chan In, 1024)
	out := make(chan Out, 1024)
	var wg sync.WaitGroup
	for i := 0; i < *workers; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			for r := range in {
				h := md5.Sum([]byte(r.Body))
				s := hex.EncodeToString(h[:])
				out <- Out{r.ID, s, classify(r.Body, s)}
			}
		}()
	}
	go func() {
		s := bufio.NewScanner(os.Stdin)
		s.Buffer(make([]byte, 1024*1024), 1024*1024)
		for s.Scan() {
			var r In
			if json.Unmarshal(s.Bytes(), &r) == nil {
				in <- r
			}
		}
		close(in)
	}()
	go func() { wg.Wait(); close(out) }()
	w := bufio.NewWriter(os.Stdout)
	defer w.Flush()
	enc := json.NewEncoder(w)
	for o := range out {
		enc.Encode(o)
	}
	fmt.Fprint(os.Stderr, "")
}
