<?php

require('vendor/autoload.php');

class DisplayTest extends PHPUnit_Framework_TestCase
{
    protected $client;

    protected function setUp()
    {
        $this->client = new GuzzleHttp\Client([
            'base_uri' => 'http://www.foo.co.uk'
        ]);
    }

    public function testGet_ValidInput_BookObject()
    {
        $response = $this->client->get('/get_data.php', [
            'query' => [
                'station' => '1',
                'days' => '200',
            ]
        ]);

        $this->assertEquals(200, $response->getStatusCode());

        //echo "BODY IS:" . $response->getBody() . "\n";
        $data = json_decode($response->getBody(), true);

        echo "COLS ARE:" . print_r($data['cols'], true) . "\n";
        echo "ROWS ARE:" . print_r(array_slice($data['rows'], 0, 5), true) . "\n";
        //$this->assertArrayHasKey('bookId', $data);
        //$this->assertEquals(42, $data['price']);
    }
}

?>
