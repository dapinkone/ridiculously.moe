package main

import (
	"bufio"
	"io/ioutil"
	"log"
	"net"
	"os"
	"path/filepath"
	"strings"
	"time"

	"github.com/disintegration/imaging"
)

func build_thumbnails(filename string) {

	// Only do things if the file exists, rather than failing hard.
	_, err := os.Stat(filename)
	if err != nil {
		if !os.IsNotExist(err) {
			log.Fatal("Fatal error getting stat of thumbnail src:", err)
		} //  else {
		// 	return
		// }
	}

	// Let's trim the input (which we expect to be full path)
	dir, filename := filepath.Split(filename)
	if _, err := os.Stat(dir + "thumbs"); err != nil {
		os.Mkdir(dir+"thumbs", 0755)
	}

	thumb := filename[:len(filename)-3] + "png"
	// Only do work if it doesn't exist.
	_, err = os.Stat(dir + "thumbs/" + thumb)
	if err != nil {
		if os.IsNotExist(err) {
			src, err := imaging.Open(dir + filename)
			if err != nil {
				// log.Printf("failed to open %s: %v", filename, err)
				return
			}

			src = imaging.Resize(src, 300, 200, imaging.Lanczos)

			if err = imaging.Save(src, dir+"thumbs/"+thumb); err != nil {
				log.Fatalf("failed to save image: %v", err)
			}
		}
	}

}

func diff(a, b []os.FileInfo) (out []string) {
	m := make(map[os.FileInfo]bool)
	// Build initial state.
	for _, item := range b {
		m[item] = true
	}

	for _, item := range a {
		if _, ok := m[item]; !ok {
			if !item.IsDir() {
				m[item] = true
				out = append(out, item.Name())
			}
		}
	}
	return out
}

type semaphore chan struct{}

func (o semaphore) Lock() {
	o <- struct{}{}
}
func (o semaphore) Unlock() {
	<-o
}

func sendIt(s semaphore, f string) {
	build_thumbnails(f)
	// log.Print(f)
	s.Unlock()
}

func watcher(dir string) {
	// Use semaphore pattern to control concurrency.
	// We open lots of files, that needs to be...restricted.
	// TODO: Abstract away to a struct "Watcher" that combines
	// functionality for reusing this stuff.
	sem := make(semaphore, 100) //struct{}, 100)
	defer close(sem)

	// Begin the work.
	base, err := os.Stat(dir)
	if err != nil {
		log.Fatal("Couldn't stat ", dir)
	}

	// We need a "safe" list, but contains is neat. Let's use a map
	// whos value uses no memory :D
	safeList := make(map[string]struct{})
	for _, k := range []string{"png", "jpg", "jpeg"} {
		safeList[k] = struct{}{}
	}

	// Build needed items for watching.
	begin := base.ModTime()
	for {
		curr, err := os.Stat(dir)
		if err != nil {
			log.Fatal("Couldn't stat inside loop..")
		}

		if curr.ModTime().After(begin) {
			// Make sure path ends in /
			if !strings.HasSuffix(dir, "/") {
				dir = dir + "/"
			}

			base, err := ioutil.ReadDir(dir)
			if err != nil {
				log.Fatal("Can't open base dir..")
			}

			thumbs, err := ioutil.ReadDir(dir + "thumbs")
			if err != nil {
				if os.IsNotExist(err) {
					os.Mkdir(dir+"thumbs", 0755)
				}
			}

			if len(thumbs) != 0 {
				new := diff(base, thumbs)
				for _, f := range new {
					if _, ok := safeList[f[len(f)-3:]]; !ok {
						// TODO: We'll have errors one day.
						continue
					}
					// Use a slot.
					sem.Lock()

					// Originally was a closure.
					go sendIt(sem, dir+f)
				}
			} else {
				// NOTE: It will not generate thumbnails on first run but
				// does it here when you add the first new file. If any thumbnails
				// are missing it will generate those along with the new file.
				for _, f := range base {
					if !f.IsDir() {
						if _, ok := safeList[f.Name()[len(f.Name())-3:]]; !ok {
							log.Println("DEBUG| Skipping ", f.Name())
							// TODO: We'll have errors one day.
							continue
						}
						// Use a slot.
						sem.Lock()
						go sendIt(sem, dir+f.Name())
					}
				}
			}
			// Change our begin time to our most recent + 1 second for leeway
			// Any excess will be caught on next pass
			begin = curr.ModTime().Add(time.Second)
		}
	}
}

func main() {
	// Build the socket.
	sock, err := net.Listen("tcp4", ":8766")
	if err != nil {
		log.Fatal("Couldn't open the socket: ", err)
	}
	defer sock.Close()

	// This has its own infinite loop in that. We shold change it.
	if len(os.Args) > 1 {
		go watcher(os.Args[1])
	}

	for {
		client, err := sock.Accept()
		if err != nil {
			log.Fatal("Socket could not accept client: ", err)
		}

		go func(c net.Conn) {
			// TODO: stuff here
			scanner := bufio.NewScanner(c)

			for scanner.Scan() {
				filename := scanner.Text()
				go build_thumbnails(filename)
			}
		}(client)
	}
}
