package main

import (
	"bufio"
	"flag"
	"log"
	"net"
	"os"
	"path/filepath"

	"github.com/disintegration/imaging"
	"strings"
)

// Useful startup flags. We should make this into a config.
var port = flag.String("bind", ":8767", "The binding on which to listen.")
var maxWorkers = flag.Uint("workers", 25, "Set the max number of concurrently open files.")
var thumbsDirectory = flag.String("dir", "<src>", "The directory in which to save thumbs. If <src>, use given directory/thumbs/filename.png")

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

func build_thumbnails(filename string) {
	// Only do things if the file exists, rather than failing hard.
	_, err := os.Stat(filename)
	if err != nil {
		if !os.IsNotExist(err) {
			log.Fatal("Fatal error getting stat of thumbnail src:", err)
		}
	}

	// Let's trim the input (which we expect to be full path)
	dir, filename := filepath.Split(filename)

	// Let's not break backwards compatibility.
	if *thumbsDirectory == "<src>" {
		*thumbsDirectory = dir + "thumbs/"
	}

	// Add a slash to end if we need to.
	if !strings.HasSuffix(*thumbsDirectory, "/") {
		*thumbsDirectory += "/"
	}

	// Now we return to our regularly scheduled broadcast.
	if _, err := os.Stat(*thumbsDirectory); err != nil {
		os.Mkdir(*thumbsDirectory, 0755)
	}

	thumb := filename[:len(filename)-3] + "png"
	src, err := imaging.Open(dir + filename)
	if err != nil {
		log.Println("Failed to open file for image processing: ", err)
		return
	}

	src = imaging.Thumbnail(src, 300, 200, imaging.Lanczos)

	outPath, err := filepath.Abs(*thumbsDirectory + thumb)
	if err != nil {
		log.Fatalf("Couldn't get absolute path of {} + {}: {}", *thumbsDirectory, thumb, err)
	}

	log.Println("Saving ", outPath)

	if err = imaging.Save(src, outPath); err != nil {
		log.Fatalf("failed to save image: %v", err)
	}
}

type Queue chan string

func queueHandler(q Queue, workers uint) {
	// This will be our limiting semaphore.
	sem := make(chan struct{}, workers)
	defer close(sem)

	// We need a "safe" list, but contains is neat. Let's use a map
	// whos value uses no memory :D
	safeList := make(map[string]struct{})
	for _, k := range []string{".png", ".jpg", ".jpeg"} {
		safeList[k] = struct{}{}
	}

	for {
		file := <-q
		// Does the file extention match our safeList?
		if _, ok := safeList[filepath.Ext(file)]; ok {
			// Get directory and prepare filename for new format.
			dir, thumb := filepath.Split(file)

			// The library we use for build_thumbnails saves as the format of our
			// file extention. It's been requested that we use PNG.
			thumb = thumb[:len(thumb)-3] + "png"

			// Let's check if the thumb exists.
			if _, err := os.Stat(dir + *thumbsDirectory + thumb); err != nil {
				if os.IsNotExist(err) {
					sem <- struct{}{}
					go func() {
						build_thumbnails(file)
						defer func() { <-sem }()
					}()
				}
			}
		}
	}
}

func main() {
	flag.Parse()

	// A queue doesn't have to be complex..
	queue := make(Queue)
	defer close(queue)

	// Build the socket.
	sock, err := net.Listen("tcp4", *port)
	if err != nil {
		log.Fatal("Couldn't open the socket: ", err)
	}
	defer sock.Close()

	// TODO: Don't be such a dirty boii
	go queueHandler(queue, *maxWorkers)

	for {
		client, err := sock.Accept()
		if err != nil {
			log.Fatal("Socket could not accept client: ", err)
		}

		log.Println("INFO| accepted", client.RemoteAddr())

		go func(c net.Conn) {
			// TODO: stuff here
			scanner := bufio.NewScanner(c)

			for scanner.Scan() {
				text := scanner.Text()
				queue <- text
			}
		}(client)
	}
}
